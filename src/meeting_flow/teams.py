from typing import List

from playwright.async_api import Page

from ..logging_utils import get_logger
from .base import MeetingFlow


logger = get_logger(__name__)


class TeamsFlow(MeetingFlow):
    async def _disable_mic_and_camera(self, page: Page) -> None:
        # Teams web UI – common selectors for mic/camera toggles
        mic_selectors = [
            '[aria-label*="Mute"]',
            '[aria-label*="Microphone"]',
            'button[data-tid="prejoin-toggle-mute"]',
        ]
        cam_selectors = [
            '[aria-label*="Turn camera off"]',
            '[aria-label*="Camera"]',
            'button[data-tid="prejoin-toggle-video"]',
        ]
        for selector in mic_selectors:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                break
        for selector in cam_selectors:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                break

    async def join_meeting(self, page: Page, meeting_url: str) -> None:
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
        await page.goto(meeting_url, wait_until="networkidle")

        # Some Teams links first show a "Continue on this browser" button
        continue_selectors = [
            'a:has-text("Continue on this browser")',
            'button:has-text("Continue on this browser")',
        ]
        for selector in continue_selectors:
            link = await page.query_selector(selector)
            if link:
                await link.click()
                break

        await page.wait_for_timeout(3000)
        await self._disable_mic_and_camera(page)

        join_selectors = [
            'button:has-text("Join now")',
            'button:has-text("Join")',
        ]
        for selector in join_selectors:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                break

    async def wait_for_meeting_end(self, page: Page) -> None:
        # Heuristic: loop until Teams shows "Call ended" or similar,
        # or page navigates away.
        while True:
            url = page.url
            if "teams.microsoft.com" not in url:
                break
            content = await page.content()
            if "Call ended" in content or "You left" in content:
                break
            await page.wait_for_timeout(5000)

    async def read_participants(self, page: Page) -> List[dict]:
        """Attempt to read participant list from the Participants panel."""
        # Open the participants pane
        people_button_selectors = [
            '[aria-label*="Participants"]',
            'button[data-tid="participant-button"]',
        ]
        for selector in people_button_selectors:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                break

        await page.wait_for_timeout(1000)
        elements = await page.query_selector_all(
            '[data-tid="participant-list-item"], [role="listitem"]'
        )
        participants: List[dict] = []
        for el in elements:
            name_el = await el.query_selector('[data-tid="participant-name"], [aria-label]')
            name = None
            if name_el:
                name = (await name_el.get_attribute("aria-label")) or (
                    await name_el.inner_text()
                )
            if name:
                participants.append({"name": name})
        return participants



