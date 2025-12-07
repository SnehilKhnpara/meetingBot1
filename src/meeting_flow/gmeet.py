from pathlib import Path
from typing import List
from datetime import datetime, timezone

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..cookie_manager import get_cookie_manager
from ..events import event_publisher
from ..logging_utils import get_logger
from .base import MeetingFlow


logger = get_logger(__name__)


class GoogleMeetFlow(MeetingFlow):
    
    async def _disable_mic_and_camera(self, page: Page) -> None:
        """Disable microphone and camera on the pre-join screen."""
        # Google Meet usually uses buttons with aria labels or data attributes.
        mic_selectors = [
            '[aria-label*="Turn off microphone"]',
            '[aria-label*="Microphone"]',
            'button[data-is-muted="false"][aria-label*="microphone"]',
        ]
        cam_selectors = [
            '[aria-label*="Turn off camera"]',
            '[aria-label*="Camera"]',
            'button[data-is-muted="false"][aria-label*="camera"]',
        ]
        
        # Disable microphone
        for selector in mic_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    logger.debug(f"Disabled microphone via selector: {selector}")
                    break
            except Exception:
                continue
        
        await page.wait_for_timeout(500)
        
        # Disable camera
        for selector in cam_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    logger.debug(f"Disabled camera via selector: {selector}")
                    break
            except Exception:
                continue

    async def _handle_prejoin_permissions(self, page: Page) -> None:
        """Handle Google Meet pre-join mic/camera permission dialog."""
        try:
            # Wait for dialog to appear - use multiple strategies to detect it
            logger.info(
                "Checking for pre-join mic/camera permission dialog",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            
            # Wait a bit for page to stabilize after navigation/sign-in
            await page.wait_for_timeout(2000)
            
            # Try to detect the dialog by looking for the text content
            dialog_detected = False
            try:
                # Wait up to 5 seconds for the dialog text to appear
                await page.wait_for_selector(
                    'text="Do you want people to hear you in the meeting?"',
                    timeout=5000,
                    state="visible"
                )
                dialog_detected = True
            except Exception:
                # Try alternative detection methods
                page_text = (await page.content()).lower()
                if "do you want people to hear you" in page_text:
                    dialog_detected = True
            
            if not dialog_detected:
                logger.info(
                    "No pre-join mic/camera dialog detected - proceeding normally",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
                return

            logger.info(
                "🔊 Pre-join permission dialog detected! Handling it now...",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            
            # Wait a bit more for dialog animation to complete
            await page.wait_for_timeout(1000)
            
            # Try multiple strategies to click the buttons
            clicked = False
            
            # Strategy 1: Try text-based button selection (most reliable)
            button_texts = [
                "Microphone allowed",
                "Camera and microphone allowed",
                "Allow",
            ]
            
            for button_text in button_texts:
                try:
                    # Try exact text match first
                    button = page.get_by_role("button", name=button_text, exact=False)
                    if await button.is_visible(timeout=2000):
                        await button.click(timeout=3000)
                        logger.info(
                            f"✅ Clicked permissions dialog button: {button_text}",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "button_text": button_text,
                                }
                            },
                        )
                        clicked = True
                        break
                except Exception:
                    continue
            
            # Strategy 2: Try CSS selectors if text-based didn't work
            if not clicked:
                button_selectors = [
                    'button:has-text("Microphone allowed")',
                    'button:has-text("Camera and microphone allowed")',
                    'button:has-text("Allow")',
                    '[role="button"]:has-text("Microphone allowed")',
                    '[role="button"]:has-text("Camera and microphone allowed")',
                ]
                
                for selector in button_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn and await btn.is_visible():
                            await btn.click()
                            button_text = await btn.inner_text()
                            logger.info(
                                f"✅ Clicked permissions dialog button via selector: {button_text}",
                                extra={
                                    "extra_data": {
                                        "meeting_id": self.meeting_id,
                                        "session_id": self.session_id,
                                        "selector": selector,
                                    }
                                },
                            )
                            clicked = True
                            break
                    except Exception:
                        continue
            
            # Strategy 3: Fallback - find any button in the dialog and click it
            if not clicked:
                try:
                    # Look for buttons inside a modal/dialog container
                    dialog_buttons = await page.query_selector_all(
                        '[role="dialog"] button, [class*="dialog"] button, [class*="modal"] button'
                    )
                    for btn in dialog_buttons:
                        btn_text = (await btn.inner_text()).strip()
                        if btn_text and ("allowed" in btn_text.lower() or "allow" in btn_text.lower()):
                            if await btn.is_visible():
                                await btn.click()
                                logger.info(
                                    f"✅ Clicked dialog button via fallback: {btn_text}",
                                    extra={
                                        "extra_data": {
                                            "meeting_id": self.meeting_id,
                                            "session_id": self.session_id,
                                        }
                                    },
                                )
                                clicked = True
                                break
                except Exception:
                    pass
            
            # Strategy 4: Last resort - close the dialog
            if not clicked:
                try:
                    # Try to find and click the close (X) button
                    close_selectors = [
                        'button[aria-label="Close"]',
                        'button[aria-label*="Close"]',
                        '[aria-label="Close"]',
                        'button:has([aria-label="Close"])',
                        'button[class*="close"]',
                    ]
                    for selector in close_selectors:
                        close_btn = await page.query_selector(selector)
                        if close_btn and await close_btn.is_visible():
                            await close_btn.click()
                            logger.info(
                                "⚠️ Closed permissions dialog via Close (X) button",
                                extra={
                                    "extra_data": {
                                        "meeting_id": self.meeting_id,
                                        "session_id": self.session_id,
                                    }
                                },
                            )
                            clicked = True
                            break
                except Exception as e:
                    logger.warning(
                        f"Could not close dialog: {e}",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                            }
                        },
                    )
            
            if not clicked:
                logger.warning(
                    "❌ Could not click any button in permissions dialog",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
            else:
                # Wait for dialog to disappear after clicking
                await page.wait_for_timeout(2000)
                
        except Exception as e:
            logger.warning(
                f"Error handling pre-join permission dialog: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )

    async def join_meeting(self, page: Page, meeting_url: str) -> None:
        logger.info(
            "Joining Google Meet",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                    "meeting_url": meeting_url,
                }
            },
        )
        
        try:
            # Navigate with timeout
            await page.goto(meeting_url, wait_until="domcontentloaded", timeout=30000)
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
        except Exception as nav_error:
            error_msg = f"Failed to navigate to meeting URL: {str(nav_error)}"
            logger.error(
                error_msg,
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(nav_error),
                    }
                },
            )
            raise ValueError(error_msg) from nav_error

        # Wait for page to load and check for errors
        await page.wait_for_timeout(3000)
        page_content = (await page.content()).lower()
        
        # Check for "can't join" error or sign-in requirement
        needs_sign_in = False
        
        if "can't join" in page_content or "you can't join" in page_content:
            # Check if it's a sign-in issue or other error
            sign_in_links = await page.query_selector_all('a[href*="accounts.google.com"], text=/sign.*in/i')
            if sign_in_links:
                needs_sign_in = True
            else:
                error_msg = "Google Meet blocked access: 'You can't join this video call'. Possible reasons: 1) Meeting requires host to admit participants, 2) Meeting URL is invalid/expired. Solution: Check meeting URL or ask host to admit you."
                logger.error(
                    error_msg,
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "current_url": page.url,
                        }
                    },
                )
                raise ValueError(error_msg)
        
        # Check for sign-in prompts (avoid invalid combined selector)
        sign_in_selectors = [
            'text="Sign in"',
            'text="Sign In"',
            '[aria-label*="Sign in"]',
            '[aria-label*="Sign In"]',
            'a[href*="accounts.google.com"]',
        ]
        for selector in sign_in_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    needs_sign_in = True
                    break
            except Exception:
                continue
        
        # If sign-in is needed, wait for manual sign-in and then continue
        if needs_sign_in:
            logger.info(
                "⚠️ SIGN-IN REQUIRED: Please complete sign-in in the browser window. Waiting up to 2 minutes...",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "message": "Waiting for sign-in completion",
                    }
                },
            )
            
            # Wait for user to sign in (poll every 5 seconds, up to 2 minutes)
            max_wait_time = 120  # 2 minutes
            check_interval = 5  # Check every 5 seconds
            waited = 0
            
            while waited < max_wait_time:
                await page.wait_for_timeout(check_interval * 1000)
                waited += check_interval
                
                # Refresh page content
                await page.reload(wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(2000)
                
                # Check if sign-in is still needed
                new_content = (await page.content()).lower()
                has_sign_in = "sign in" in new_content or "can't join" in new_content
                has_meeting_ui = "join" in new_content or "microphone" in new_content or "camera" in new_content
                
                if not has_sign_in and has_meeting_ui:
                    logger.info(
                        "✅ Sign-in detected! Saving cookies and continuing with meeting join...",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "waited_seconds": waited,
                            }
                        },
                    )
                    # Automatically save cookies after successful sign-in
                    try:
                        context = page.context
                        storage_state = await context.storage_state()
                        cookie_manager = get_cookie_manager()
                        cookie_file = await cookie_manager.save_cookies("gmeet", storage_state)
                        logger.info(
                            "✅ Cookies saved automatically for future meetings",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "cookie_file": cookie_file,
                                }
                            },
                        )
                        await event_publisher.publish_event(
                            "cookies_saved",
                            {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "platform": "gmeet",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to save cookies (meeting will still continue): {e}",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "error": str(e),
                                }
                            },
                        )
                    break
                
                if waited % 15 == 0:  # Log every 15 seconds
                    logger.info(
                        f"Still waiting for sign-in... ({waited}/{max_wait_time} seconds)",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                            }
                        },
                    )
            else:
                # Timeout reached
                error_msg = "Sign-in timeout: Please sign in to Google manually and try joining again. The browser window is still open - sign in there and retry."
                logger.error(
                    error_msg,
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "waited_seconds": waited,
                        }
                    },
                )
                raise ValueError(error_msg)
            
            # After sign-in, wait a bit more for page to stabilize
            await page.wait_for_timeout(3000)
            page_content = (await page.content()).lower()

        # Handle pre-join mic/camera permission dialog if it appears (first check)
        await self._handle_prejoin_permissions(page)
        
        # Wait a bit for any dialogs to appear
        await page.wait_for_timeout(3000)
        
        # Handle dialog again in case it appeared after first check
        await self._handle_prejoin_permissions(page)

        # Try to disable mic and camera
        try:
            await self._disable_mic_and_camera(page)
        except Exception as e:
            logger.warning(
                f"Could not disable mic/camera: {str(e)}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )

        # Wait for page to fully load before looking for join button
        await page.wait_for_timeout(3000)
        
        # Final check for dialog right before joining
        await self._handle_prejoin_permissions(page)
        await page.wait_for_timeout(1000)
        
        # Try multiple join button selectors with timeouts - more comprehensive list
        join_button_selectors = [
            'button:has-text("Join now")',
            'button:has-text("Ask to join")',
            'button:has-text("Join")',
            '[aria-label*="Join now"]',
            '[aria-label*="Ask to join"]',
            '[aria-label*="Join meeting"]',
            '[aria-label*="Join"]',
            '[jsname="Qx7uuf"]',  # Common Google Meet join button
            'button[data-tooltip*="Join"]',
            'div[role="button"]:has-text("Join now")',
            'div[role="button"]:has-text("Ask to join")',
            '[data-mdc-dialog-action="join"]',
            'button.joining',
        ]
        
        join_success = False
        last_error = None
        
        for selector in join_button_selectors:
            try:
                # Wait for selector with longer timeout
                btn = await page.wait_for_selector(selector, timeout=10000, state="visible")
                if btn and await btn.is_visible():
                    # Scroll into view if needed
                    await btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await btn.click()
                    logger.info(
                        f"Clicked join button: {selector}",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "selector": selector,
                            }
                        },
                    )
                    join_success = True
                    break
            except Exception as e:
                last_error = str(e)
                continue
        
        # Try alternative: Click by coordinates if button found but not clickable
        if not join_success:
            try:
                # Look for any join-related text on page
                join_elements = await page.query_selector_all('button, div[role="button"], [aria-label*="Join"], [aria-label*="join"]')
                for elem in join_elements:
                    text = await elem.inner_text()
                    aria_label = await elem.get_attribute("aria-label") or ""
                    if text and ("join" in text.lower() or "join" in aria_label.lower()):
                        try:
                            await elem.scroll_into_view_if_needed()
                            await page.wait_for_timeout(500)
                            await elem.click()
                            logger.info(
                                f"Clicked join element by text: {text[:50]}",
                                extra={
                                    "extra_data": {
                                        "meeting_id": self.meeting_id,
                                        "session_id": self.session_id,
                                    }
                                },
                            )
                            join_success = True
                            break
                        except Exception:
                            continue
            except Exception:
                pass

        if not join_success:
            # Take screenshot for debugging
            try:
                screenshot_path = f"data/debug_{self.session_id}.png"
                Path("data").mkdir(exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(
                    "Saved screenshot for debugging",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "screenshot": screenshot_path,
                        }
                    },
                )
            except Exception as sce:
                logger.warning(f"Could not save screenshot: {sce}")
            
            # Get page title and URL for better error message
            page_title = await page.title()
            current_url = page.url
            
            error_msg = (
                f"Could not find join button on Google Meet page. "
                f"Current URL: {current_url}, Page title: {page_title}. "
                f"Possible causes: 1) Meeting requires sign-in (check browser window), "
                f"2) Meeting UI changed, 3) Meeting URL invalid/expired. "
                f"Check screenshot at data/debug_{self.session_id}.png for details. "
                f"Last error: {last_error}"
            )
            logger.error(
                error_msg,
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "current_url": current_url,
                        "page_title": page_title,
                        "last_error": last_error,
                    }
                },
            )
            raise ValueError(error_msg)

        # Wait a bit to see if join succeeded
        await page.wait_for_timeout(3000)
        
        # Check if we're actually in the meeting
        current_url = page.url
        if "meet.google.com" not in current_url:
            error_msg = f"Not in Google Meet after join attempt. Current URL: {current_url}"
            logger.error(
                error_msg,
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "current_url": current_url,
                    }
                },
            )
            raise ValueError(error_msg)
        
        # Enable closed captions after joining
        try:
            from ..closed_captions import ClosedCaptionsExtractor
            cc_extractor = ClosedCaptionsExtractor(platform="gmeet")
            await cc_extractor.enable_cc(page)
        except Exception as e:
            logger.debug(f"Could not enable CC (non-critical): {e}")
        
        # Save cookies after successful join to keep them fresh
        try:
            context = page.context
            storage_state = await context.storage_state()
            cookie_manager = get_cookie_manager()
            settings = get_settings()
            if settings.use_stored_cookies:
                await cookie_manager.save_cookies("gmeet", storage_state)
                logger.debug(
                    "Cookies refreshed after successful join",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
        except Exception as e:
            # Non-critical - don't fail join if cookie save fails
            logger.debug(f"Could not refresh cookies (non-critical): {e}")

    async def wait_for_meeting_end(self, page: Page) -> None:
        """Wait for meeting to end - uses enhanced detector if available."""
        try:
            from ..meeting_end_detector import MeetingEndDetector
            detector = MeetingEndDetector(
                platform="gmeet",
                meeting_id=self.meeting_id if hasattr(self, 'meeting_id') else "unknown",
                session_id=self.session_id if hasattr(self, 'session_id') else "unknown"
            )
            await detector.wait_for_meeting_end(page)
        except Exception:
            # Fallback to simple detection
            while True:
                url = page.url
                if "meet.google.com" not in url:
                    break
                content = await page.content()
                if "You left the meeting" in content or "Meeting ended" in content:
                    break
                await page.wait_for_timeout(5000)

    async def read_participants(self, page: Page) -> List[dict]:
        """
        Read participants using ROBUST extractor.
        
        Uses multiple methods to ensure we get ALL participants.
        """
        # Use robust extractor first
        try:
            from ..participant_extractor_robust import RobustParticipantExtractor
            robust_extractor = RobustParticipantExtractor()
            participants = await robust_extractor.extract_participants(page)
            
            if participants:
                logger.info(
                    f"ROBUST extraction found {len(participants)} participants",
                    extra={
                        "extra_data": {
                            "participant_count": len(participants),
                            "participants": [p.get("name") for p in participants],
                        }
                    },
                )
                return participants
        except Exception as e:
            logger.warning(f"Robust extractor failed, using fallback: {e}")
        
        # Fallback to original extractor
        try:
            from ..participant_extractor import ParticipantExtractor
            extractor = ParticipantExtractor(platform="gmeet")
            participants = await extractor.extract_participants(page)
            return participants
        except Exception as e:
            logger.warning(f"Original extractor also failed: {e}")
            return []
    
    async def read_participants_old(self, page: Page) -> List[dict]:
        """Attempt to read participant list from the People panel."""
        try:
            people_button = await page.query_selector(
                '[aria-label*="Show everyone"], [aria-label*="People"]'
            )
            if people_button:
                await people_button.click()
        except PlaywrightTimeoutError:
            return []

        await page.wait_for_timeout(2000)  # Wait longer for panel to load
        
        participants: List[dict] = []
        
        # Strategy 1: Look for participant items with data-self-name attribute (most reliable)
        try:
            elements_with_name = await page.query_selector_all('[data-self-name]')
            for el in elements_with_name:
                try:
                    name = await el.get_attribute("data-self-name")
                    if name and name.strip():
                        from ..participant_name_filter import clean_participant_name
                        cleaned_name = clean_participant_name(name)
                        if cleaned_name:
                            participants.append({"name": cleaned_name})
                except Exception:
                    continue
        except Exception:
            pass
        
        # Strategy 2: If no results, try list items
        if not participants:
            try:
                elements = await page.query_selector_all('[role="listitem"], [data-participant-id]')
                for el in elements:
                    try:
                        # Try to find name element within list item
                        name_el = await el.query_selector('[data-self-name], span[dir="auto"], [aria-label]')
                        if name_el:
                            name = (
                                await name_el.get_attribute("data-self-name")
                                or await name_el.get_attribute("aria-label")
                                or await name_el.inner_text()
                            )
                            if name and name.strip():
                                from ..participant_name_filter import clean_participant_name
                                cleaned_name = clean_participant_name(name)
                                if cleaned_name:
                                    participants.append({"name": cleaned_name})
                    except Exception:
                        continue
            except Exception:
                pass
        
        logger.debug(
            f"Extracted {len(participants)} participants",
            extra={
                "extra_data": {
                    "participant_count": len(participants),
                    "participants": [p.get("name") for p in participants],
                }
            },
        )
        
        return participants



