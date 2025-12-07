from abc import ABC, abstractmethod
from typing import List, Protocol

from playwright.async_api import Page


class MeetingFlow(ABC):
    """Abstract base for platform-specific join and monitoring flows."""

    def __init__(self, meeting_id: str, session_id: str) -> None:
        self.meeting_id = meeting_id
        self.session_id = session_id

    @abstractmethod
    async def join_meeting(self, page: Page, meeting_url: str) -> None:
        """Navigate to meeting URL, disable mic/cam, and click join."""

    @abstractmethod
    async def wait_for_meeting_end(self, page: Page) -> None:
        """Block until meeting ends according to platform heuristics."""

    @abstractmethod
    async def read_participants(self, page: Page) -> List[dict]:
        """Read the current list of participants from the UI."""


class EventPublisher(Protocol):
    async def publish_event(self, event_type: str, payload: dict) -> None: ...



