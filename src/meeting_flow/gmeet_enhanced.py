"""
Production-grade Google Meet flow using the enhanced join system.

This flow:
- Uses persistent profiles per session
- Attempts "Join now" first, falls back to "Ask to join" if needed
- Allows waiting room scenarios (host approval may be required)
- Provides detailed error messages with screenshots
- Validates login state before attempting join
"""
from typing import List
from playwright.async_api import Page

from ..google_meet.join_meeting import GoogleMeetJoinFlow, GoogleMeetJoinError
from ..logging_utils import get_logger
from .base import MeetingFlow


logger = get_logger(__name__)


class GoogleMeetFlowEnhanced(MeetingFlow):
    """Production-grade Google Meet flow."""
    
    def __init__(self, meeting_id: str, session_id: str):
        super().__init__(meeting_id, session_id)
        self.join_flow = GoogleMeetJoinFlow(meeting_id, session_id)
    
    async def join_meeting(self, page: Page, meeting_url: str) -> None:
        """
        Join Google Meet meeting with robust error handling.
        
        Raises:
            ValueError: If join fails (will be logged with details)
        """
        try:
            await self.join_flow.join(page, meeting_url)
            
            # Enable closed captions after joining
            await self._enable_closed_captions(page)
            
        except GoogleMeetJoinError as e:
            # Convert to ValueError for compatibility with existing error handling
            error_msg = str(e)
            logger.error(
                error_msg,
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error_type": "GoogleMeetJoinError",
                    }
                },
            )
            raise ValueError(error_msg) from e
    
    async def _enable_closed_captions(self, page: Page) -> None:
        """Enable closed captions in Google Meet."""
        try:
            from ..closed_captions import ClosedCaptionsExtractor
            
            cc_extractor = ClosedCaptionsExtractor(platform="gmeet")
            enabled = await cc_extractor.enable_cc(page)
            
            if enabled:
                logger.info(
                    "Closed captions enabled successfully",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
            else:
                logger.warning(
                    "Could not enable closed captions",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
        except Exception as e:
            logger.warning(
                f"Error enabling closed captions: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
    
    async def wait_for_meeting_end(self, page: Page) -> None:
        """Wait for meeting to end."""
        from ..meeting_end_detector import MeetingEndDetector
        detector = MeetingEndDetector(
            platform="gmeet",
            meeting_id=self.meeting_id,
            session_id=self.session_id
        )
        await detector.wait_for_meeting_end(page)
    
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

