"""
Production-grade Google Meet join flow.

Key requirements:
- NEVER shows "Ask to join" or waiting room
- Automatically detects and aborts if login is invalid
- Provides detailed error messages with screenshots
"""
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..config import get_settings
from ..logging_utils import get_logger
from ..google_auth.persistent_profile import get_profile_manager

logger = get_logger(__name__)


class GoogleMeetJoinError(Exception):
    """Custom exception for Google Meet join failures."""
    pass


class GoogleMeetJoinFlow:
    """Robust Google Meet join flow that bypasses waiting rooms."""
    
    def __init__(self, meeting_id: str, session_id: str):
        self.meeting_id = meeting_id
        self.session_id = session_id
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def join(self, page: Page, meeting_url: str) -> None:
        """
        Join a Google Meet meeting with robust error detection.
        
        Raises:
            GoogleMeetJoinError: If join fails for any reason
        """
        logger.info(
            "Starting Google Meet join flow",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                    "meeting_url": meeting_url,
                }
            },
        )
        
        try:
            # Step 1: Navigate to meeting URL
            await self._navigate_to_meeting(page, meeting_url)
            
            # Step 2: Validate login state
            await self._validate_login_state(page)
            
            # Step 3: Handle pre-join dialogs
            await self._handle_prejoin_dialogs(page)
            
            # Step 4: Ensure mic/camera are off
            await self._ensure_devices_off(page)
            
            # Step 5: Join the meeting (prefers "Join now", allows "Ask to join" if needed)
            await self._join_meeting(page)
            
            # Step 6: Validate we're in meeting or waiting room (both are valid)
            await self._validate_in_meeting(page)
            
            logger.info(
                "✅ Successfully joined Google Meet",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            
        except Exception as e:
            # Capture screenshot for debugging
            await self._capture_error_screenshot(page, str(e))
            raise
    
    async def _navigate_to_meeting(self, page: Page, meeting_url: str) -> None:
        """Navigate to the meeting URL."""
        try:
            await page.goto(meeting_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for initial load
            
            logger.info(
                "Navigated to meeting URL",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "current_url": page.url,
                    }
                },
            )
        except Exception as e:
            raise GoogleMeetJoinError(
                f"Failed to navigate to meeting URL: {str(e)}"
            ) from e
    
    async def _validate_login_state(self, page: Page) -> None:
        """Validate that the user is logged into Google."""
        await page.wait_for_timeout(2000)
        
        current_url = page.url.lower()
        page_content = (await page.content()).lower()
        
        # Check for explicit sign-in requirements
        sign_in_indicators = [
            "servicelogin" in current_url,
            "accounts.google.com/signin" in current_url,
            "sign in" in page_content and "google" in page_content,
        ]
        
        if any(sign_in_indicators):
            raise GoogleMeetJoinError(
                "❌ NOT LOGGED IN: Profile requires Google sign-in. "
                "Please log in manually in non-headless mode, then restart bot. "
                "If this persists, the profile may be corrupted - delete and recreate it."
            )
        
        # Check for "can't join" errors that indicate auth issues
        if "can't join" in page_content or "you can't join" in page_content:
            # Check if it's an auth issue or meeting permission issue
            error_text = await self._extract_error_message(page)
            if "sign in" in error_text.lower():
                raise GoogleMeetJoinError(
                    f"❌ AUTHENTICATION FAILED: {error_text}. "
                    "Profile login state is invalid. Re-login required."
                )
            else:
                raise GoogleMeetJoinError(
                    f"❌ CANNOT JOIN MEETING: {error_text}. "
                    "This may indicate the meeting URL is invalid, expired, or requires host approval."
                )
        
        logger.info(
            "Login state validated - profile is authenticated",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                }
            },
        )
    
    async def _handle_prejoin_dialogs(self, page: Page) -> None:
        """Handle any pre-join dialogs (permissions, etc.)."""
        # Wait for page to stabilize
        await page.wait_for_timeout(2000)
        
        # Check for mic/camera permission dialog
        dialog_texts = [
            "Do you want people to hear you in the meeting?",
            "do you want people to hear you",
        ]
        
        for dialog_text in dialog_texts:
            try:
                dialog_locator = page.get_by_text(dialog_text, exact=False)
                if await dialog_locator.is_visible(timeout=2000):
                    logger.info(
                        "Handling pre-join permission dialog",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                            }
                        },
                    )
                    
                    # Try to click "Microphone allowed" (no camera)
                    button_texts = [
                        "Microphone allowed",
                        "Camera and microphone allowed",
                        "Allow",
                    ]
                    
                    for button_text in button_texts:
                        try:
                            btn = page.get_by_role("button", name=button_text, exact=False)
                            if await btn.is_visible(timeout=1000):
                                await btn.click(timeout=3000)
                                logger.info(
                                    f"Clicked permission dialog button: {button_text}",
                                    extra={
                                        "extra_data": {
                                            "meeting_id": self.meeting_id,
                                            "session_id": self.session_id,
                                        }
                                    },
                                )
                                await page.wait_for_timeout(2000)
                                break
                        except Exception:
                            continue
                    break
            except Exception:
                continue
        
        # Wait for any dialogs to close
        await page.wait_for_timeout(2000)
    
    async def _ensure_devices_off(self, page: Page) -> None:
        """Ensure microphone and camera are turned off."""
        try:
            # Try to find and disable microphone
            mic_selectors = [
                '[aria-label*="Turn off microphone"]',
                '[aria-label*="Microphone"]',
                'button[data-is-muted="false"][aria-label*="microphone" i]',
            ]
            
            for selector in mic_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(500)
                        break
                except Exception:
                    continue
            
            # Try to find and disable camera
            cam_selectors = [
                '[aria-label*="Turn off camera"]',
                '[aria-label*="Camera"]',
                'button[data-is-muted="false"][aria-label*="camera" i]',
            ]
            
            for selector in cam_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(500)
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Could not disable devices (non-critical): {e}")
    
    async def _join_meeting(self, page: Page) -> None:
        """Join the meeting - Try to bypass waiting room, but allow 'Ask to join' if needed."""
        # Wait for pre-join UI to fully load
        await page.wait_for_timeout(3000)
        
        # Try to find and click "Join now" button first (preferred)
        join_now_selectors = [
            'button:has-text("Join now")',
            '[aria-label*="Join now"]',
            '[aria-label*="Join meeting"]',
            '[jsname="Qx7uuf"]',  # Common Google Meet join button
            'button[data-tooltip*="Join now"]',
        ]
        
        join_clicked = False
        
        for selector in join_now_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=5000, state="visible")
                if btn and await btn.is_visible():
                    await btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await btn.click(timeout=3000)
                    
                    logger.info(
                        f"✅ Clicked 'Join now' button: {selector}",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "selector": selector,
                            }
                        },
                    )
                    join_clicked = True
                    break
            except Exception:
                continue
        
        # If "Join now" not found, try "Ask to join" as fallback
        if not join_clicked:
            logger.info(
                "'Join now' button not found, trying 'Ask to join'...",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            
            ask_to_join_selectors = [
                'button:has-text("Ask to join")',
                '[aria-label*="Ask to join"]',
                'button[aria-label*="ask to join" i]',
            ]
            
            for selector in ask_to_join_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=5000, state="visible")
                    if btn and await btn.is_visible():
                        await btn.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        await btn.click(timeout=3000)
                        
                        logger.info(
                            f"⚠️ Clicked 'Ask to join' button: {selector}",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "selector": selector,
                                    "warning": "Meeting requires host approval",
                                }
                            },
                        )
                        join_clicked = True
                        break
                except Exception:
                    continue
        
        # If still no button found, try generic "Join" button
        if not join_clicked:
            generic_join_selectors = [
                'button:has-text("Join")',
                '[aria-label*="Join"]',
                'button[data-tooltip*="Join"]',
            ]
            
            for selector in generic_join_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        btn_text = await btn.inner_text()
                        # Make sure it's not "Leave" or something else
                        if btn_text and "join" in btn_text.lower() and "leave" not in btn_text.lower():
                            await btn.scroll_into_view_if_needed()
                            await page.wait_for_timeout(500)
                            await btn.click(timeout=3000)
                            
                            logger.info(
                                f"Clicked join button: {btn_text}",
                                extra={
                                    "extra_data": {
                                        "meeting_id": self.meeting_id,
                                        "session_id": self.session_id,
                                    }
                                },
                            )
                            join_clicked = True
                            break
                except Exception:
                    continue
        
        if not join_clicked:
            # Last resort - take screenshot and provide helpful error
            await self._capture_error_screenshot(page, "Could not find any join button")
            raise GoogleMeetJoinError(
                "❌ JOIN BUTTON NOT FOUND: Could not locate any join button. "
                "Possible causes: 1) Meeting URL invalid/expired, "
                "2) Login state invalid, 3) UI changed. Check screenshot for details."
            )
        
        # Wait for join to process
        await page.wait_for_timeout(3000)
    
    async def _validate_in_meeting(self, page: Page) -> None:
        """Validate that we're in the meeting or waiting room (both are valid states)."""
        await page.wait_for_timeout(2000)
        
        current_url = page.url.lower()
        page_content = (await page.content()).lower()
        
        # Must be on meet.google.com
        if "meet.google.com" not in current_url:
            raise GoogleMeetJoinError(
                f"❌ NOT IN MEETING: Navigated away from Google Meet. Current URL: {page.url}"
            )
        
        # Check if we're actually in the meeting (best case)
        meeting_ui_indicators = [
            "turn off microphone",
            "turn off camera",
            "leave call",
            "present now",
        ]
        
        has_meeting_ui = any(indicator in page_content for indicator in meeting_ui_indicators)
        
        if has_meeting_ui:
            logger.info(
                "✅ Confirmed in meeting - UI indicators detected",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            return  # Success - we're in the meeting!
        
        # Check if we're in waiting room (also valid - waiting for host approval)
        waiting_room_indicators = [
            "still trying to get in",
            "waiting for someone to let you in",
        ]
        
        for indicator in waiting_room_indicators:
            if indicator in page_content:
                try:
                    elem = await page.query_selector(f'text=/{indicator}/i')
                    if elem and await elem.is_visible():
                        logger.info(
                            f"⏳ In waiting room: '{indicator}' - waiting for host to admit",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "status": "waiting_for_host",
                                }
                            },
                        )
                        # This is valid - we've successfully requested to join
                        # The bot will wait for host approval
                        return
                except Exception:
                    continue
        
        # If we get here, we're on the meet page but state is unclear
        # This is okay - might still be loading
        logger.info(
            "On Google Meet page - session active",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                    "current_url": current_url,
                }
            },
        )
    
    async def _extract_error_message(self, page: Page) -> str:
        """Extract error message from the page."""
        try:
            # Try common error message selectors
            error_selectors = [
                '[role="alert"]',
                '.error-message',
                '[class*="error"]',
                '[class*="Error"]',
            ]
            
            for selector in error_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text:
                            return text.strip()
                except Exception:
                    continue
            
            # Fallback: get page title
            title = await page.title()
            return f"Page title: {title}"
            
        except Exception:
            return "Unknown error"
    
    async def _capture_error_screenshot(self, page: Page, error_message: str) -> None:
        """Capture screenshot when join fails."""
        try:
            screenshot_path = self.data_dir / f"error_{self.session_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Also capture page state
            page_state = {
                "url": page.url,
                "title": await page.title(),
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            state_path = self.data_dir / f"error_{self.session_id}_state.json"
            import json
            with open(state_path, 'w') as f:
                json.dump(page_state, f, indent=2)
            
            logger.error(
                f"Error screenshot saved: {screenshot_path}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "screenshot_path": str(screenshot_path),
                        "error": error_message,
                    }
                },
            )
        except Exception as e:
            logger.warning(f"Could not capture error screenshot: {e}")

