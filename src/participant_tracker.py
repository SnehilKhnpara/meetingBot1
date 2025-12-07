"""
Enhanced participant tracking with active speaker detection.

Tracks participants with join/leave times, roles, and active speaker status.
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .logging_utils import get_logger
from .participant_name_filter import is_valid_participant_name, clean_participant_name

logger = get_logger(__name__)

# DEPRECATED: Use ParticipantExtractor instead for production-grade extraction
# This class is kept for backward compatibility


class ParticipantTracker:
    """Enhanced participant tracking for Google Meet and Teams."""
    
    def __init__(self, platform: str):
        self.platform = platform.lower()
    
    async def get_participants(self, page: Page) -> List[Dict]:
        """
        Get full participant list with metadata.
        
        Returns list of participant dictionaries with:
        - name: Display name
        - join_time: When they joined (if detectable)
        - role: host/guest/presenter (if detectable)
        - is_speaking: Whether currently speaking (if detectable)
        """
        if self.platform == "gmeet":
            return await self._get_gmeet_participants(page)
        elif self.platform == "teams":
            return await self._get_teams_participants(page)
        else:
            logger.warning(f"Unknown platform: {self.platform}, using basic extraction")
            return await self._get_basic_participants(page)
    
    async def _get_gmeet_participants(self, page: Page) -> List[Dict]:
        """Extract participants from Google Meet UI."""
        participants = []
        
        try:
            # Step 1: Open participants panel if not already open
            await self._ensure_participants_panel_open(page)
            
            # Wait for panel to load
            await page.wait_for_timeout(1500)
            
            # Step 2: Extract participants from the panel
            # Use more specific selectors to get actual participant items
            # Try to find participant items in the People panel specifically
            participant_elements = []
            
            # Method 1: Look for participant items within the People panel
            try:
                # Find the People panel container first
                people_panel = await page.query_selector(
                    '[aria-label*="People" i], [aria-label*="Show everyone" i], [role="dialog"][aria-label*="People" i]'
                )
                
                if people_panel:
                    # Look for participant items within the panel
                    elements = await people_panel.query_selector_all(
                        '[role="listitem"]:has([data-self-name]), '
                        '[data-participant-id], '
                        '[role="listitem"]:has(span[dir="auto"])'
                    )
                    if elements:
                        participant_elements = elements
                        logger.debug(f"Found {len(elements)} participants in People panel")
            except Exception as e:
                logger.debug(f"Could not find People panel container: {e}")
            
            # Method 2: Try general selectors (fallback)
            if not participant_elements:
                participant_selectors = [
                    '[role="listitem"][data-self-name]',
                    '[data-participant-id]',
                ]
                
                for selector in participant_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            participant_elements = elements
                            logger.debug(f"Found participants using selector: {selector}")
                            break
                    except Exception:
                        continue
            
            # Step 3: Extract data from each participant element
            for idx, element in enumerate(participant_elements):
                try:
                    participant_data = await self._extract_gmeet_participant_data(
                        page, element, idx
                    )
                    if participant_data and participant_data.get("name"):
                        # Filter out UI notifications
                        name = participant_data.get("name")
                        cleaned_name = clean_participant_name(name)
                        if cleaned_name:
                            participant_data["name"] = cleaned_name
                            participants.append(participant_data)
                        else:
                            logger.debug(f"Filtered out UI element as participant: {name}")
                except Exception as e:
                    logger.debug(f"Could not extract participant {idx}: {e}")
                    continue
            
            # Step 4: Detect active speaker
            active_speaker = await self._detect_gmeet_active_speaker(page)
            if active_speaker:
                # Update participant with active speaker status
                for p in participants:
                    if p.get("name") == active_speaker:
                        p["is_speaking"] = True
                    else:
                        p["is_speaking"] = False
            
        except Exception as e:
            logger.warning(
                f"Error extracting Google Meet participants: {e}",
                extra={
                    "extra_data": {
                        "platform": "gmeet",
                        "error": str(e),
                    }
                },
            )
        
        return participants
    
    async def _get_teams_participants(self, page: Page) -> List[Dict]:
        """Extract participants from Microsoft Teams UI."""
        participants = []
        
        try:
            # Open participants panel in Teams
            await self._ensure_teams_participants_panel_open(page)
            await page.wait_for_timeout(1500)
            
            # Teams uses different selectors
            participant_elements = await page.query_selector_all(
                '[data-tid="participant-item"], [role="listitem"]'
            )
            
            for idx, element in enumerate(participant_elements):
                try:
                    participant_data = await self._extract_teams_participant_data(
                        page, element, idx
                    )
                    if participant_data and participant_data.get("name"):
                        participants.append(participant_data)
                except Exception as e:
                    logger.debug(f"Could not extract Teams participant {idx}: {e}")
                    continue
            
            # Detect active speaker in Teams
            active_speaker = await self._detect_teams_active_speaker(page)
            if active_speaker:
                for p in participants:
                    if p.get("name") == active_speaker:
                        p["is_speaking"] = True
                    else:
                        p["is_speaking"] = False
        
        except Exception as e:
            logger.warning(
                f"Error extracting Teams participants: {e}",
                extra={
                    "extra_data": {
                        "platform": "teams",
                        "error": str(e),
                    }
                },
            )
        
        return participants
    
    async def _get_basic_participants(self, page: Page) -> List[Dict]:
        """Basic participant extraction as fallback."""
        participants = []
        try:
            elements = await page.query_selector_all('[role="listitem"]')
            for element in elements:
                try:
                    name_el = await element.query_selector('[aria-label], [data-self-name]')
                    if name_el:
                        name = (
                            await name_el.get_attribute("aria-label")
                            or await name_el.inner_text()
                        )
                        if name and name.strip():
                            participants.append({"name": name.strip()})
                except Exception:
                    continue
        except Exception:
            pass
        return participants
    
    async def _ensure_participants_panel_open(self, page: Page) -> None:
        """Ensure Google Meet participants panel is open."""
        # Check if panel is already open
        panel_visible = await page.query_selector('[aria-label*="People"]:visible, [aria-label*="Show everyone"]:visible')
        if panel_visible:
            return
        
        # Try to open panel
        button_selectors = [
            '[aria-label*="Show everyone"]',
            '[aria-label*="People"]',
            '[data-tooltip*="People"]',
            'button[jsname="Qx7uuf"]',
        ]
        
        for selector in button_selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click(timeout=3000)
                    await page.wait_for_timeout(500)
                    return
            except Exception:
                continue
        
        logger.debug("Could not open participants panel - may already be open or unavailable")
    
    async def _ensure_teams_participants_panel_open(self, page: Page) -> None:
        """Ensure Teams participants panel is open."""
        # Teams participants panel logic
        button_selectors = [
            '[aria-label*="Show participants"]',
            '[data-tid="roster-button"]',
            'button[title*="participants" i]',
        ]
        
        for selector in button_selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click(timeout=3000)
                    await page.wait_for_timeout(500)
                    return
            except Exception:
                continue
    
    async def _extract_gmeet_participant_data(
        self, page: Page, element, index: int
    ) -> Optional[Dict]:
        """Extract participant data from a Google Meet participant element."""
        participant = {}
        
        try:
            # Extract name - prioritize data-self-name attribute (most reliable)
            name = None
            
            # First, try data-self-name attribute (most reliable for Google Meet)
            try:
                name = await element.get_attribute("data-self-name")
                if name:
                    name = name.strip()
            except Exception:
                pass
            
            # If not found, try to find name element within the participant item
            if not name:
                name_selectors = [
                    'span[data-self-name]',
                    'div[data-self-name]',
                    '[data-self-name]',
                    'span[dir="auto"]',
                ]
                
                for selector in name_selectors:
                    try:
                        name_el = await element.query_selector(selector)
                        if name_el:
                            name = (
                                await name_el.get_attribute("data-self-name")
                                or await name_el.get_attribute("aria-label")
                                or await name_el.inner_text()
                            )
                            if name and name.strip():
                                name = name.strip()
                                break
                    except Exception:
                        continue
            
            # Last resort: get all text and extract name
            if not name:
                try:
                    # Get all text from element
                    all_text = await element.inner_text()
                    if all_text:
                        # Split by newlines and take first line (usually the name)
                        lines = [line.strip() for line in all_text.split("\n") if line.strip()]
                        if lines:
                            # First non-empty line is usually the name
                            potential_name = lines[0]
                            # Filter out obvious UI elements
                            if is_valid_participant_name(potential_name):
                                name = potential_name
                except Exception:
                    pass
            
            if not name or not name.strip():
                return None
            
            # Clean and validate name - filter out UI notifications
            cleaned_name = clean_participant_name(name)
            if not cleaned_name:
                # Name is a UI element, skip it
                logger.debug(f"Filtered out UI notification: {name}")
                return None
            
            participant["name"] = cleaned_name
            
            # Extract role (host/presenter indicator)
            role_indicators = await element.query_selector_all(
                '[aria-label*="host" i], [aria-label*="presenter" i], [aria-label*="organizer" i]'
            )
            if role_indicators:
                participant["role"] = "host"
            else:
                participant["role"] = "guest"
            
            # Check for speaking indicator
            speaking_indicators = await element.query_selector_all(
                '[aria-label*="speaking" i], [class*="speaking" i], [data-speaking="true"]'
            )
            participant["is_speaking"] = len(speaking_indicators) > 0
            
            # Try to extract join time (may not be available)
            # This is typically not visible in UI, so we'll rely on tracking
            
        except Exception as e:
            logger.debug(f"Error extracting participant data: {e}")
            return None
        
        return participant if participant.get("name") else None
    
    async def _extract_teams_participant_data(
        self, page: Page, element, index: int
    ) -> Optional[Dict]:
        """Extract participant data from a Teams participant element."""
        participant = {}
        
        try:
            # Extract name
            name_el = await element.query_selector(
                '[data-tid="participant-name"], [aria-label], span'
            )
            if name_el:
                name = (
                    await name_el.get_attribute("aria-label")
                    or await name_el.inner_text()
                )
                if name:
                    participant["name"] = name.strip()
            
            # Extract role
            role_el = await element.query_selector('[data-tid="participant-role"]')
            if role_el:
                role_text = await role_el.inner_text()
                if "organizer" in role_text.lower() or "host" in role_text.lower():
                    participant["role"] = "host"
                else:
                    participant["role"] = "guest"
            else:
                participant["role"] = "guest"
            
            # Check for active speaker indicator
            active_frame = await element.query_selector('[class*="active" i], [class*="speaking" i]')
            participant["is_speaking"] = active_frame is not None
        
        except Exception as e:
            logger.debug(f"Error extracting Teams participant data: {e}")
            return None
        
        return participant if participant.get("name") else None
    
    async def _detect_gmeet_active_speaker(self, page: Page) -> Optional[str]:
        """Detect who is currently speaking in Google Meet."""
        try:
            # Look for speaking indicators in the participant list
            speaking_elements = await page.query_selector_all(
                '[aria-label*="speaking" i], [class*="speaking" i], [data-speaking="true"]'
            )
            
            for element in speaking_elements:
                try:
                    # Try to find the participant name associated with this speaking indicator
                    participant_container = await element.evaluate_handle(
                        "(el) => el.closest('[role=\"listitem\"], [data-participant-id]')"
                    )
                    if participant_container:
                        name_el = await participant_container.query_selector(
                            '[data-self-name], [aria-label]'
                        )
                        if name_el:
                            name = (
                                await name_el.get_attribute("aria-label")
                                or await name_el.inner_text()
                            )
                            if name:
                                return name.strip()
                except Exception:
                    continue
            
            # Alternative: Check main video area for active speaker highlight
            active_speaker_frame = await page.query_selector(
                '[class*="speaking" i], [data-speaking="true"]'
            )
            if active_speaker_frame:
                # Try to extract name from video frame
                name_attr = await active_speaker_frame.get_attribute("aria-label")
                if name_attr and "speaking" in name_attr.lower():
                    # Extract name from aria-label like "John Doe is speaking"
                    parts = name_attr.split("is speaking")
                    if parts:
                        return parts[0].strip()
        
        except Exception as e:
            logger.debug(f"Error detecting active speaker: {e}")
        
        return None
    
    async def _detect_teams_active_speaker(self, page: Page) -> Optional[str]:
        """Detect who is currently speaking in Teams."""
        try:
            # Teams shows active speaker with highlighted frame
            active_frame = await page.query_selector(
                '[class*="active-speaker" i], [class*="speaking" i], [data-active-speaker="true"]'
            )
            
            if active_frame:
                # Try to extract name from active frame
                name_el = await active_frame.query_selector(
                    '[data-tid="participant-name"], [aria-label]'
                )
                if name_el:
                    name = (
                        await name_el.get_attribute("aria-label")
                        or await name_el.inner_text()
                    )
                    if name:
                        return name.strip()
        
        except Exception as e:
            logger.debug(f"Error detecting Teams active speaker: {e}")
        
        return None
    
    def count_other_participants(self, participants: List[Dict]) -> int:
        """
        Count participants excluding the bot/user.
        
        Filters out participants with "(You)" in their name.
        
        Returns:
            Number of other participants (excluding bot/user)
        """
        other_participants = [
            p for p in participants
            if p.get("name") and "(You)" not in p.get("name", "")
        ]
        return len(other_participants)
    
    def is_only_bot_user(self, participants: List[Dict]) -> bool:
        """
        Check if only the bot/user remains in the meeting.
        
        Returns:
            True if only bot/user is present (no other participants)
        """
        other_count = self.count_other_participants(participants)
        return other_count == 0 and len(participants) <= 1

