"""
Enhanced Microsoft Teams flow with improved participant tracking and meeting end detection.

Uses the new ParticipantTracker and MeetingEndDetector modules.
"""
from typing import List
from playwright.async_api import Page

from ..participant_tracker import ParticipantTracker
from ..meeting_end_detector import MeetingEndDetector
from ..logging_utils import get_logger
from .base import MeetingFlow


logger = get_logger(__name__)


class TeamsFlowEnhanced(MeetingFlow):
    """Enhanced Microsoft Teams flow with improved tracking and detection."""
    
    def __init__(self, meeting_id: str, session_id: str):
        super().__init__(meeting_id, session_id)
        self.tracker = ParticipantTracker(platform="teams")
        self.end_detector = MeetingEndDetector(
            platform="teams",
            meeting_id=meeting_id,
            session_id=session_id
        )
    
    async def _disable_mic_and_camera(self, page: Page) -> None:
        """Disable microphone and camera on the pre-join screen."""
        mic_selectors = [
            '[aria-label*="Mute" i]',
            '[aria-label*="Microphone" i]',
            'button[data-tid="prejoin-toggle-mute"]',
            '[data-tid="toggle-mute"]',
        ]
        cam_selectors = [
            '[aria-label*="Turn camera off" i]',
            '[aria-label*="Camera" i]',
            'button[data-tid="prejoin-toggle-video"]',
            '[data-tid="toggle-video"]',
        ]
        
        # Disable microphone
        for selector in mic_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click(timeout=3000)
                    logger.debug("Disabled microphone in Teams")
                    break
            except Exception:
                continue
        
        # Disable camera
        for selector in cam_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click(timeout=3000)
                    logger.debug("Disabled camera in Teams")
                    break
            except Exception:
                continue
    
    async def join_meeting(self, page: Page, meeting_url: str) -> None:
        """Join Microsoft Teams meeting with enhanced error handling."""
        logger.info(
            "Joining Microsoft Teams meeting",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                    "meeting_url": meeting_url,
                }
            },
        )
        
        try:
            # Navigate to meeting URL
            await page.goto(meeting_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Handle "Continue on this browser" button if present
            continue_selectors = [
                'a:has-text("Continue on this browser")',
                'button:has-text("Continue on this browser")',
                '[aria-label*="Continue on this browser" i]',
            ]
            
            for selector in continue_selectors:
                try:
                    link = await page.wait_for_selector(selector, timeout=5000, state="visible")
                    if link:
                        await link.click()
                        await page.wait_for_timeout(2000)
                        logger.debug("Clicked 'Continue on this browser'")
                        break
                except Exception:
                    continue
            
            # Wait for pre-join screen to load
            await page.wait_for_timeout(2000)
            
            # Disable mic and camera
            await self._disable_mic_and_camera(page)
            await page.wait_for_timeout(1000)
            
            # Click join button
            join_selectors = [
                'button:has-text("Join now")',
                'button:has-text("Join")',
                '[aria-label*="Join now" i]',
                '[aria-label*="Join meeting" i]',
                '[data-tid="prejoin-join-button"]',
            ]
            
            join_clicked = False
            for selector in join_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=5000, state="visible")
                    if btn:
                        await btn.scroll_into_view_if_needed()
                        await btn.click(timeout=3000)
                        logger.info(
                            f"Clicked join button: {selector}",
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
                raise ValueError(
                    "Could not find or click join button in Teams. "
                    "Meeting URL may be invalid or UI may have changed."
                )
            
            # Wait for join to process
            await page.wait_for_timeout(3000)
            
            # Verify we're in the meeting
            current_url = page.url.lower()
            if "teams.microsoft.com" not in current_url or "/call/" not in current_url:
                logger.warning(
                    f"May not be in Teams meeting. Current URL: {page.url}",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "current_url": page.url,
                        }
                    },
                )
            
            logger.info(
                "Successfully joined Teams meeting",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            
        except Exception as e:
            error_msg = f"Failed to join Teams meeting: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
            raise ValueError(error_msg) from e
    
    async def wait_for_meeting_end(self, page: Page) -> None:
        """Wait for meeting to end using enhanced detection."""
        await self.end_detector.wait_for_meeting_end(page)
        # Attempt clean exit
        await self.end_detector.leave_meeting_cleanly(page)
    
    async def read_participants(self, page: Page) -> List[dict]:
        """Read participants using enhanced tracker with active speaker detection."""
        return await self.tracker.get_participants(page)



