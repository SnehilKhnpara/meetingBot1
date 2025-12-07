"""
Production-grade participant extraction for Google Meet and Teams.

Uses stable DOM selectors and robust filtering to extract ONLY real participant names.
Filters out all UI elements, notifications, and system text.
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone

from playwright.async_api import Page

from .logging_utils import get_logger
from .participant_name_filter import clean_participant_name, is_valid_participant_name

logger = get_logger(__name__)


class ParticipantExtractor:
    """
    Production-grade participant extraction with robust filtering.
    
    Uses multiple strategies to find real participants and filters out:
    - UI notifications
    - System messages
    - Control buttons
    - Tooltips
    - Settings panels
    """
    
    def __init__(self, platform: str):
        self.platform = platform.lower()
    
    async def extract_participants(self, page: Page) -> List[Dict]:
        """
        Extract real participants from the meeting UI.
        
        Returns:
            List of participant dicts with: name, role, is_speaking
        """
        if self.platform == "gmeet":
            return await self._extract_gmeet_participants(page)
        elif self.platform == "teams":
            return await self._extract_teams_participants(page)
        else:
            return await self._extract_generic_participants(page)
    
    async def _extract_gmeet_participants(self, page: Page) -> List[Dict]:
        """
        CRITICAL: Extract ONLY real participants from Google Meet.
        
        Uses multiple strategies and HARD FILTERING to ensure UI elements are never included.
        """
        participants = []
        raw_names_seen = []  # For debugging
        
        try:
            # Step 1: Ensure People panel is open
            await self._ensure_people_panel_open(page)
            await page.wait_for_timeout(2000)  # Wait for panel to fully load
            
            # Step 2: Use multiple extraction strategies
            # Strategy A: Direct data-self-name attributes (most reliable)
            participants_a = await self._extract_via_data_self_name(page)
            
            # Strategy B: Participant list items with name spans
            participants_b = await self._extract_via_list_items(page)
            
            # Strategy C: Contributors section
            participants_c = await self._extract_via_contributors(page)
            
            # Merge and deduplicate with STRICT filtering
            all_participants = {}
            for p_list in [participants_a, participants_b, participants_c]:
                for p in p_list:
                    name = p.get("name", "").strip()
                    raw_names_seen.append(name)  # Track for debugging
                    
                    if not name:
                        continue
                    
                    # CRITICAL: Hard filter - must pass validation
                    if not is_valid_participant_name(name):
                        logger.debug(
                            f"Filtered out invalid participant name: {name}",
                            extra={
                                "extra_data": {
                                    "platform": "gmeet",
                                    "filtered_name": name,
                                    "reason": "failed_validation",
                                }
                            },
                        )
                        continue
                    
                    # Clean the name
                    cleaned_name = clean_participant_name(name)
                    if not cleaned_name:
                        continue
                    
                    # Use first occurrence, or merge data
                    if cleaned_name not in all_participants:
                        all_participants[cleaned_name] = {
                            **p,
                            "name": cleaned_name,  # Use cleaned name
                        }
                    else:
                        # Merge: keep role if available, keep speaking status
                        existing = all_participants[cleaned_name]
                        if p.get("role") and not existing.get("role"):
                            existing["role"] = p["role"]
                        if p.get("is_speaking"):
                            existing["is_speaking"] = True
            
            participants = list(all_participants.values())
            
            # Developer-level logging: Show what was filtered
            logger.debug(
                f"DEVELOPER: Participant extraction - {len(raw_names_seen)} raw names, {len(participants)} valid participants",
                extra={
                    "extra_data": {
                        "platform": "gmeet",
                        "raw_names_count": len(raw_names_seen),
                        "valid_participants_count": len(participants),
                        "raw_names": raw_names_seen[:10],  # First 10 for debugging
                        "valid_names": [p.get("name") for p in participants],
                    }
                },
            )
            
            # Step 3: Detect active speaker
            active_speaker_name = await self._detect_active_speaker_gmeet(page)
            if active_speaker_name:
                for p in participants:
                    if p.get("name") == active_speaker_name:
                        p["is_speaking"] = True
                    else:
                        p["is_speaking"] = False
            
            logger.debug(
                f"Extracted {len(participants)} real participants from Google Meet",
                extra={
                    "extra_data": {
                        "participant_count": len(participants),
                        "participants": [p.get("name") for p in participants],
                    }
                },
            )
            
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
    
    async def _extract_via_data_self_name(self, page: Page) -> List[Dict]:
        """Extract using data-self-name attribute (most reliable)."""
        participants = []
        
        try:
            # Find all elements with data-self-name attribute
            elements = await page.query_selector_all('[data-self-name]')
            
            for element in elements:
                try:
                    name = await element.get_attribute("data-self-name")
                    if not name:
                        continue
                    
                    # Clean and validate
                    cleaned_name = clean_participant_name(name)
                    if not cleaned_name:
                        continue
                    
                    # Check if this is a participant item (not a button or control)
                    parent = await element.evaluate_handle("el => el.closest('[role=\"listitem\"]')")
                    if not parent:
                        # Not in a list item, might be a control element
                        continue
                    
                    # Extract role
                    role = "guest"
                    role_indicators = await element.query_selector_all(
                        '[aria-label*="host" i], [aria-label*="organizer" i], [aria-label*="presenter" i]'
                    )
                    if role_indicators:
                        role = "host"
                    
                    participants.append({
                        "name": cleaned_name,
                        "role": role,
                        "is_speaking": False,
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in _extract_via_data_self_name: {e}")
        
        return participants
    
    async def _extract_via_list_items(self, page: Page) -> List[Dict]:
        """Extract from participant list items."""
        participants = []
        
        try:
            # Find participant list items in People panel
            list_items = await page.query_selector_all(
                '[role="listitem"]:has([data-self-name]), '
                '[role="listitem"]:has(span[dir="auto"]), '
                '[data-participant-id]'
            )
            
            for item in list_items:
                try:
                    # Try to find name element within list item
                    name_element = await item.query_selector(
                        '[data-self-name], span[dir="auto"], [aria-label]'
                    )
                    
                    if not name_element:
                        continue
                    
                    # Get name
                    name = (
                        await name_element.get_attribute("data-self-name")
                        or await name_element.get_attribute("aria-label")
                        or await name_element.inner_text()
                    )
                    
                    if not name:
                        continue
                    
                    # Clean and validate
                    cleaned_name = clean_participant_name(name)
                    if not cleaned_name:
                        continue
                    
                    # Check if this is a real participant (not UI element)
                    # Get full text of list item to check for UI indicators
                    item_text = await item.inner_text()
                    if item_text:
                        item_text_lower = item_text.lower()
                        # Skip if contains UI indicators
                        ui_indicators = [
                            "backgrounds", "effects", "microphone", "camera",
                            "settings", "options", "can't", "your "
                        ]
                        if any(indicator in item_text_lower for indicator in ui_indicators):
                            continue
                    
                    # Extract role
                    role = "guest"
                    if "host" in item_text_lower or "organizer" in item_text_lower:
                        role = "host"
                    
                    # Check for speaking indicator
                    is_speaking = False
                    speaking_indicators = await item.query_selector_all(
                        '[class*="speaking" i], [aria-label*="speaking" i]'
                    )
                    if speaking_indicators:
                        is_speaking = True
                    
                    participants.append({
                        "name": cleaned_name,
                        "role": role,
                        "is_speaking": is_speaking,
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in _extract_via_list_items: {e}")
        
        return participants
    
    async def _extract_via_contributors(self, page: Page) -> List[Dict]:
        """Extract from Contributors section."""
        participants = []
        
        try:
            # Find Contributors section
            contributors_section = await page.query_selector(
                '[aria-label*="Contributors" i], [class*="contributor" i]'
            )
            
            if not contributors_section:
                return participants
            
            # Find participant items within Contributors section
            items = await contributors_section.query_selector_all(
                '[role="listitem"], [data-self-name]'
            )
            
            for item in items:
                try:
                    name_element = await item.query_selector('[data-self-name], span')
                    if not name_element:
                        continue
                    
                    name = (
                        await name_element.get_attribute("data-self-name")
                        or await name_element.inner_text()
                    )
                    
                    if not name:
                        continue
                    
                    cleaned_name = clean_participant_name(name)
                    if cleaned_name:
                        participants.append({
                            "name": cleaned_name,
                            "role": "guest",
                            "is_speaking": False,
                        })
                        
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in _extract_via_contributors: {e}")
        
        return participants
    
    async def _detect_active_speaker_gmeet(self, page: Page) -> Optional[str]:
        """Detect active speaker from Google Meet UI."""
        try:
            # Look for speaking indicators
            speaking_elements = await page.query_selector_all(
                '[class*="speaking" i], [aria-label*="speaking" i], [data-speaking="true"]'
            )
            
            for element in speaking_elements:
                try:
                    # Find associated participant name
                    name_element = await element.query_selector('[data-self-name]')
                    if name_element:
                        name = await name_element.get_attribute("data-self-name")
                        if name:
                            cleaned = clean_participant_name(name)
                            if cleaned:
                                return cleaned
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return None
    
    async def _ensure_people_panel_open(self, page: Page) -> None:
        """Ensure People panel is open."""
        try:
            # Check if panel is already open
            panel_visible = await page.query_selector(
                '[aria-label*="People" i]:visible, [aria-label*="Show everyone" i]:visible'
            )
            if panel_visible:
                return
            
            # Try to open panel
            button_selectors = [
                '[aria-label*="Show everyone"]',
                '[aria-label*="People"]',
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
                    
        except Exception:
            pass
    
    async def _extract_teams_participants(self, page: Page) -> List[Dict]:
        """Extract participants from Microsoft Teams."""
        participants = []
        
        try:
            # Open participants panel
            await self._ensure_teams_panel_open(page)
            await page.wait_for_timeout(2000)
            
            # Find participant items
            items = await page.query_selector_all(
                '[data-tid="participant-item"], [role="listitem"]'
            )
            
            for item in items:
                try:
                    name_element = await item.query_selector(
                        '[data-tid="participant-name"], [aria-label]'
                    )
                    if not name_element:
                        continue
                    
                    name = (
                        await name_element.get_attribute("aria-label")
                        or await name_element.inner_text()
                    )
                    
                    if not name:
                        continue
                    
                    cleaned_name = clean_participant_name(name)
                    if cleaned_name:
                        # Extract role
                        role = "guest"
                        role_element = await item.query_selector('[data-tid="participant-role"]')
                        if role_element:
                            role_text = await role_element.inner_text()
                            if "organizer" in role_text.lower() or "host" in role_text.lower():
                                role = "host"
                        
                        # Check speaking status
                        is_speaking = False
                        speaking_indicator = await item.query_selector('[class*="active" i]')
                        if speaking_indicator:
                            is_speaking = True
                        
                        participants.append({
                            "name": cleaned_name,
                            "role": role,
                            "is_speaking": is_speaking,
                        })
                        
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting Teams participants: {e}")
        
        return participants
    
    async def _ensure_teams_panel_open(self, page: Page) -> None:
        """Ensure Teams participants panel is open."""
        try:
            button_selectors = [
                '[aria-label*="Show participants"]',
                '[data-tid="roster-button"]',
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
        except Exception:
            pass
    
    async def _extract_generic_participants(self, page: Page) -> List[Dict]:
        """Generic extraction fallback."""
        participants = []
        
        try:
            elements = await page.query_selector_all('[role="listitem"]')
            for element in elements:
                try:
                    name_element = await element.query_selector('[aria-label], [data-self-name]')
                    if name_element:
                        name = (
                            await name_element.get_attribute("aria-label")
                            or await name_element.get_attribute("data-self-name")
                            or await name_element.inner_text()
                        )
                        if name:
                            cleaned = clean_participant_name(name)
                            if cleaned:
                                participants.append({
                                    "name": cleaned,
                                    "role": "guest",
                                    "is_speaking": False,
                                })
                except Exception:
                    continue
        except Exception:
            pass
        
        return participants

