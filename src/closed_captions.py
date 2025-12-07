"""
Closed Captions / Live Subtitles extraction for Google Meet and Teams.

Automatically enables CC and extracts transcript text in real-time.
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone

from playwright.async_api import Page

from .logging_utils import get_logger

logger = get_logger(__name__)


class ClosedCaptionsExtractor:
    """Extract closed captions from meeting platforms."""
    
    def __init__(self, platform: str):
        self.platform = platform.lower()
        self.transcript: List[Dict] = []
    
    async def enable_cc(self, page: Page) -> bool:
        """
        Enable closed captions in the meeting.
        
        Returns:
            True if CC was enabled, False otherwise
        """
        if self.platform == "gmeet":
            return await self._enable_gmeet_cc(page)
        elif self.platform == "teams":
            return await self._enable_teams_cc(page)
        else:
            return False
    
    async def _enable_gmeet_cc(self, page: Page) -> bool:
        """Enable closed captions in Google Meet."""
        try:
            # Google Meet CC button selectors
            cc_selectors = [
                '[aria-label*="Turn on captions" i]',
                '[aria-label*="Captions" i]',
                'button[data-tooltip*="captions" i]',
                'button[aria-label*="CC" i]',
                '[data-tooltip="Turn on captions"]',
                '[data-tooltip="Turn off captions"]',  # Check if already on
            ]
            
            # Try to find and click CC button
            for selector in cc_selectors:
                try:
                    cc_button = await page.query_selector(selector)
                    if cc_button:
                        # Check if already enabled
                        aria_label = await cc_button.get_attribute("aria-label") or ""
                        if "turn off" in aria_label.lower() or "off" in aria_label.lower():
                            logger.info(
                                "Closed captions already enabled",
                                extra={
                                    "extra_data": {
                                        "platform": "gmeet",
                                    }
                                },
                            )
                            return True
                        
                        # Click to enable
                        await cc_button.click()
                        await page.wait_for_timeout(1000)
                        
                        logger.info(
                            "Closed captions enabled",
                            extra={
                                "extra_data": {
                                    "platform": "gmeet",
                                    "selector": selector,
                                }
                            },
                        )
                        return True
                except Exception:
                    continue
            
            # Alternative: Use keyboard shortcut (Ctrl+Shift+C)
            try:
                await page.keyboard.press("Control+Shift+C")
                await page.wait_for_timeout(1000)
                logger.info(
                    "Closed captions enabled via keyboard shortcut",
                    extra={
                        "extra_data": {
                            "platform": "gmeet",
                            "method": "keyboard_shortcut",
                        }
                    },
                )
                return True
            except Exception as e:
                logger.debug(f"Keyboard shortcut failed: {e}")
            
            logger.warning(
                "Could not enable closed captions - button not found",
                extra={
                    "extra_data": {
                        "platform": "gmeet",
                    }
                },
            )
            return False
            
        except Exception as e:
            logger.warning(
                f"Error enabling closed captions: {e}",
                extra={
                    "extra_data": {
                        "platform": "gmeet",
                        "error": str(e),
                    }
                },
            )
            return False
    
    async def _enable_teams_cc(self, page: Page) -> bool:
        """Enable closed captions in Microsoft Teams."""
        try:
            # Teams CC button selectors
            cc_selectors = [
                '[aria-label*="Turn on live captions" i]',
                '[aria-label*="Live captions" i]',
                'button[aria-label*="captions" i]',
                '[data-tid*="captions" i]',
            ]
            
            for selector in cc_selectors:
                try:
                    cc_button = await page.query_selector(selector)
                    if cc_button:
                        await cc_button.click()
                        await page.wait_for_timeout(1000)
                        logger.info(
                            "Closed captions enabled",
                            extra={
                                "extra_data": {
                                    "platform": "teams",
                                    "selector": selector,
                                }
                            },
                        )
                        return True
                except Exception:
                    continue
            
            logger.warning(
                "Could not enable closed captions - button not found",
                extra={
                    "extra_data": {
                        "platform": "teams",
                    }
                },
            )
            return False
            
        except Exception as e:
            logger.warning(
                f"Error enabling closed captions: {e}",
                extra={
                    "extra_data": {
                        "platform": "teams",
                        "error": str(e),
                    }
                },
            )
            return False
    
    async def extract_subtitles(self, page: Page) -> List[str]:
        """
        Extract current subtitle text from the page.
        
        Returns:
            List of subtitle lines currently visible
        """
        if self.platform == "gmeet":
            return await self._extract_gmeet_subtitles(page)
        elif self.platform == "teams":
            return await self._extract_teams_subtitles(page)
        else:
            return []
    
    async def _extract_gmeet_subtitles(self, page: Page) -> List[str]:
        """Extract subtitles from Google Meet."""
        subtitles = []
        
        try:
            # Google Meet subtitle selectors
            subtitle_selectors = [
                '[class*="subtitle" i]',
                '[class*="caption" i]',
                '[id*="subtitle" i]',
                '[id*="caption" i]',
                '[data-caption-text]',
                'div[role="log"]',  # CC area often uses log role
            ]
            
            for selector in subtitle_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if text and text.strip():
                            subtitles.append(text.strip())
                except Exception:
                    continue
            
            # Also try to find subtitle container
            try:
                # Google Meet CC is usually in a specific container
                cc_container = await page.query_selector('[class*="captions" i], [class*="subtitle" i]')
                if cc_container:
                    text = await cc_container.inner_text()
                    if text and text.strip():
                        subtitles.append(text.strip())
            except Exception:
                pass
            
            # Remove duplicates and empty strings
            subtitles = list(dict.fromkeys([s for s in subtitles if s]))
            
        except Exception as e:
            logger.debug(f"Error extracting subtitles: {e}")
        
        return subtitles
    
    async def _extract_teams_subtitles(self, page: Page) -> List[str]:
        """Extract subtitles from Microsoft Teams."""
        subtitles = []
        
        try:
            # Teams subtitle selectors
            subtitle_selectors = [
                '[class*="caption" i]',
                '[class*="subtitle" i]',
                '[data-tid*="caption" i]',
                '[aria-label*="caption" i]',
            ]
            
            for selector in subtitle_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if text and text.strip():
                            subtitles.append(text.strip())
                except Exception:
                    continue
            
            # Remove duplicates and empty strings
            subtitles = list(dict.fromkeys([s for s in subtitles if s]))
            
        except Exception as e:
            logger.debug(f"Error extracting subtitles: {e}")
        
        return subtitles
    
    async def poll_subtitles(self, page: Page, interval_seconds: int = 5) -> None:
        """
        Poll for subtitles and add them to transcript.
        
        Args:
            page: Playwright page
            interval_seconds: How often to poll for new subtitles
        """
        subtitles = await self.extract_subtitles(page)
        
        for subtitle_text in subtitles:
            # Check if we already have this subtitle (avoid duplicates)
            if not any(
                entry.get("text") == subtitle_text
                for entry in self.transcript
            ):
                self.transcript.append({
                    "text": subtitle_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                logger.debug(
                    f"New subtitle: {subtitle_text}",
                    extra={
                        "extra_data": {
                            "platform": self.platform,
                            "subtitle_text": subtitle_text,
                        }
                    },
                )
    
    def get_transcript_summary(self) -> str:
        """
        Get a summary of the transcript.
        
        Returns:
            Combined transcript text
        """
        if not self.transcript:
            return ""
        
        return "\n".join(entry["text"] for entry in self.transcript)


