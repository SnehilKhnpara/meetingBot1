"""
Enhanced meeting end detection with screenshot capture and clean exit.

Detects when meetings end and performs graceful cleanup.
"""
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .config import get_settings
from .logging_utils import get_logger

logger = get_logger(__name__)


class MeetingEndDetector:
    """Enhanced meeting end detection for Google Meet and Teams."""
    
    def __init__(self, platform: str, meeting_id: str, session_id: str):
        self.platform = platform.lower()
        self.meeting_id = meeting_id
        self.session_id = session_id
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def wait_for_meeting_end(self, page: Page) -> None:
        """
        Wait for meeting to end with enhanced detection.
        
        Checks multiple indicators:
        - Meeting end messages
        - Navigation away from meeting URL
        - Disconnection states
        - Empty meeting states
        """
        logger.info(
            "Waiting for meeting to end",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                    "platform": self.platform,
                }
            },
        )
        
        consecutive_empty_checks = 0
        max_empty_checks = 3  # 15 seconds of empty state
        
        while True:
            try:
                # Check if meeting has ended
                if await self._check_meeting_ended(page):
                    logger.info(
                        "Meeting end detected",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                            }
                        },
                    )
                    break
                
                # Check if disconnected
                if await self._check_disconnected(page):
                    logger.warning(
                        "Meeting disconnection detected",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                            }
                        },
                    )
                    await self._capture_screenshot(page, "disconnection")
                    break
                
                # Check if meeting is empty (only bot/user remains)
                if await self._check_meeting_empty(page):
                    consecutive_empty_checks += 1
                    if consecutive_empty_checks >= max_empty_checks:
                        logger.info(
                            "Meeting is empty (only bot/user) - leaving automatically",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "reason": "only_bot_remaining",
                                }
                            },
                        )
                        # Developer-level logging: Meeting end detection
                        logger.info(
                            "DEVELOPER: Meeting end detected - empty meeting confirmed",
                            extra={
                                "extra_data": {
                                    "meeting_id": self.meeting_id,
                                    "session_id": self.session_id,
                                    "reason": "only_bot_remaining",
                                    "consecutive_empty_checks": consecutive_empty_checks,
                                    "max_empty_checks": max_empty_checks,
                                }
                            },
                        )
                        
                        await self._capture_screenshot(page, "empty_meeting")
                        # Leave the meeting since only bot/user is present
                        await self.leave_meeting_cleanly(page)
                        break
                else:
                    consecutive_empty_checks = 0
                
                await page.wait_for_timeout(5000)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(
                    f"Error checking meeting state: {e}",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "error": str(e),
                        }
                    },
                )
                await self._capture_screenshot(page, "error")
                await asyncio.sleep(5)
    
    async def _check_meeting_ended(self, page: Page) -> bool:
        """Check if meeting has ended using platform-specific indicators."""
        if self.platform == "gmeet":
            return await self._check_gmeet_ended(page)
        elif self.platform == "teams":
            return await self._check_teams_ended(page)
        else:
            return await self._check_generic_ended(page)
    
    async def _check_gmeet_ended(self, page: Page) -> bool:
        """Check if Google Meet meeting has ended."""
        current_url = page.url.lower()
        
        # Check URL - if not on meet.google.com, meeting likely ended
        if "meet.google.com" not in current_url:
            return True
        
        try:
            page_content = (await page.content()).lower()
            
            # Check for end messages
            end_indicators = [
                "you left the meeting",
                "meeting ended",
                "the meeting has ended",
                "everyone has left",
                "call ended",
                "meeting was ended",
            ]
            
            for indicator in end_indicators:
                if indicator in page_content:
                    return True
            
            # Check for end screen elements
            end_selectors = [
                '[data-message="You left the meeting"]',
                '[aria-label*="meeting ended" i]',
                '[class*="end-screen" i]',
                '[class*="left-meeting" i]',
            ]
            
            for selector in end_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        return True
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"Error checking Google Meet end state: {e}")
        
        return False
    
    async def _check_teams_ended(self, page: Page) -> bool:
        """Check if Teams meeting has ended."""
        current_url = page.url.lower()
        
        # Check URL
        if "teams.microsoft.com" not in current_url or "/call/" not in current_url:
            return True
        
        try:
            page_content = (await page.content()).lower()
            
            # Check for end messages
            end_indicators = [
                "call ended",
                "meeting ended",
                "you left the meeting",
                "the call has ended",
                "everyone has left",
            ]
            
            for indicator in end_indicators:
                if indicator in page_content:
                    return True
            
            # Check for end screen elements
            end_selectors = [
                '[data-tid="call-ended"]',
                '[aria-label*="call ended" i]',
                '[class*="call-ended" i]',
            ]
            
            for selector in end_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        return True
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"Error checking Teams end state: {e}")
        
        return False
    
    async def _check_generic_ended(self, page: Page) -> bool:
        """Generic end check for unknown platforms."""
        try:
            page_content = (await page.content()).lower()
            end_phrases = [
                "left the meeting",
                "meeting ended",
                "call ended",
            ]
            return any(phrase in page_content for phrase in end_phrases)
        except Exception:
            return False
    
    async def _check_disconnected(self, page: Page) -> bool:
        """Check if meeting has been disconnected."""
        try:
            page_content = (await page.content()).lower()
            
            disconnect_indicators = [
                "trying to reconnect",
                "connection lost",
                "disconnected",
                "reconnecting",
                "network error",
            ]
            
            for indicator in disconnect_indicators:
                if indicator in page_content:
                    # Check if reconnecting or permanently disconnected
                    if "trying to reconnect" in page_content or "reconnecting" in page_content:
                        # Wait a bit to see if reconnection succeeds
                        await page.wait_for_timeout(10000)
                        # Check again
                        updated_content = (await page.content()).lower()
                        if any(ind in updated_content for ind in disconnect_indicators):
                            return True  # Still disconnected after waiting
                    else:
                        return True  # Permanent disconnect
            
        except Exception:
            pass
        
        return False
    
    async def _check_meeting_empty(self, page: Page) -> bool:
        """Check if meeting is empty (only bot/user remains - no other participants)."""
        try:
            if self.platform == "gmeet":
                return await self._check_gmeet_empty(page)
            elif self.platform == "teams":
                return await self._check_teams_empty(page)
            else:
                return await self._check_generic_empty(page)
        except Exception as e:
            logger.debug(f"Error checking empty meeting: {e}")
            return False
    
    async def _check_gmeet_empty(self, page: Page) -> bool:
        """
        CRITICAL: Check if Google Meet is empty (ONLY bot/user, NO real participants).
        
        This must be accurate - bot should ONLY leave when truly alone.
        """
        try:
            # Step 1: Check for "You're the only one" message
            content = (await page.content()).lower()
            empty_indicators = [
                "you're the only one",
                "you are the only one",
                "waiting for others",
                "no one else is here",
            ]
            
            for indicator in empty_indicators:
                if indicator in content:
                    logger.debug(
                        "Google Meet empty message detected",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "indicator": indicator,
                            }
                        },
                    )
                    # Don't return True yet - verify with participant count
            
            # Step 2: CRITICAL - Check participant badge count FIRST (most reliable)
            # The badge shows the actual count even if extraction fails
            badge_count = await self._get_participant_badge_count(page)
            
            logger.info(
                f"MeetingEndDetector: Badge shows {badge_count} participants",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "badge_count": badge_count,
                    }
                },
            )
            
            # CRITICAL: If badge shows > 1, meeting is NOT empty (bot + at least one other)
            if badge_count > 1:
                logger.info(
                    f"MeetingEndDetector: Badge shows {badge_count} participants - meeting NOT empty",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "badge_count": badge_count,
                            "decision": "not_empty",
                            "reason": "badge_count_gt_1",
                        }
                    },
                )
                return False  # Meeting is NOT empty
            
            # Step 3: CRITICAL - Verify with actual participant extraction
            # Use ROBUST extractor (same as session_manager) to ensure consistency
            try:
                from .participant_extractor_robust import RobustParticipantExtractor
                extractor = RobustParticipantExtractor()
                participants = await extractor.extract_participants(page)
            except Exception as e:
                logger.warning(f"Robust extractor failed, using fallback: {e}")
                # Fallback to original extractor
                from .participant_extractor import ParticipantExtractor
                extractor = ParticipantExtractor(platform="gmeet")
                participants = await extractor.extract_participants(page)
            
            # CRITICAL: If badge shows participants but extraction found 0, use badge count
            if badge_count > 0 and len(participants) == 0:
                logger.warning(
                    f"MeetingEndDetector: Badge shows {badge_count} but extraction found 0 - using badge count",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "badge_count": badge_count,
                            "extracted_count": len(participants),
                            "decision": "not_empty",
                            "reason": "badge_count_fallback",
                        }
                    },
                )
                return False  # Meeting is NOT empty (badge shows participants)
            
            # Filter to get ONLY real participants (exclude bot/user)
            from .participant_name_filter import clean_participant_name
            
            real_participants = []
            bot_participants = []
            
            for p in participants:
                name = p.get("name", "").strip()
                if not name:
                    continue
                
                # Check if it's the bot/user
                is_bot = "(You)" in name or name.lower() == "meeting bot"
                if is_bot:
                    bot_participants.append(p)
                    continue
                
                # Check if it's a placeholder from badge fallback
                if p.get("source") == "badge_count_fallback":
                    # This is a placeholder - count it as a real participant
                    real_participants.append(p)
                    continue
                
                # Everything else is a real participant (robust extractor already filtered UI)
                real_participants.append(p)
            
            num_real = len(real_participants)
            num_bot = len(bot_participants)
            total = len(participants)
            
            logger.info(
                f"MeetingEndDetector: Empty check - Badge: {badge_count}, Total: {total}, Real: {num_real}, Bot: {num_bot}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "badge_count": badge_count,
                        "real_participants": num_real,
                        "bot_participants": num_bot,
                        "total_participants": total,
                        "participant_names": [p.get("name") for p in participants],
                    }
                },
            )
            
            # CRITICAL CHECK 1: If total > 1, meeting is NOT empty
            if total > 1:
                logger.info(
                    f"MeetingEndDetector: Total participants {total} > 1 - meeting NOT empty",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "total_participants": total,
                            "decision": "not_empty",
                            "reason": "total_gt_1",
                        }
                    },
                )
                return False
            
            # CRITICAL CHECK 2: If real participants > 0, meeting is NOT empty
            if num_real > 0:
                logger.info(
                    f"MeetingEndDetector: Found {num_real} real participants - meeting NOT empty",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "real_participants": num_real,
                            "decision": "not_empty",
                            "reason": "real_participants_gt_0",
                        }
                    },
                )
                return False
            
            # CRITICAL CHECK 3: Only return True if NO real participants AND total <= 1
            # AND the remaining participant (if any) is the bot
            from .config import get_settings
            settings = get_settings()
            bot_display_name = settings.bot_display_name
            
            remaining_is_bot = False
            if total == 1:
                remaining_name = participants[0].get("name", "").strip()
                if "(You)" in remaining_name:
                    remaining_is_bot = True
                else:
                    cleaned_remaining = clean_participant_name(remaining_name)
                    if cleaned_remaining and cleaned_remaining.lower() == bot_display_name.lower():
                        remaining_is_bot = True
            
            # Only return True if ALL conditions are met
            if num_real == 0 and (total == 0 or (total == 1 and remaining_is_bot)) and badge_count <= 1:
                logger.info(
                    "MeetingEndDetector: Verified empty meeting - NO real participants, only bot remains",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "real_participants": num_real,
                            "total_participants": total,
                            "badge_count": badge_count,
                            "remaining_is_bot": remaining_is_bot,
                            "bot_display_name": bot_display_name,
                            "verification": "passed",
                        }
                    },
                )
                return True
            else:
                # If any check fails, meeting is NOT empty
                logger.info(
                    f"MeetingEndDetector: Meeting NOT empty - badge: {badge_count}, total: {total}, real: {num_real}",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "badge_count": badge_count,
                            "total_participants": total,
                            "real_participants": num_real,
                            "decision": "not_empty",
                            "reason": "checks_failed",
                        }
                    },
                )
                return False
            
        except Exception as e:
            logger.warning(
                f"Error checking empty meeting: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
            return False  # On error, assume meeting is NOT empty (safer)
    
    async def _get_participant_badge_count(self, page: Page) -> int:
        """
        Get participant count from the badge/button.
        
        This is CRITICAL - the badge shows the actual count even if extraction fails.
        """
        try:
            # Try multiple selectors for participant badge
            badge_selectors = [
                'button[aria-label*="People" i]',
                'button[aria-label*="participant" i]',
                '[data-participant-count]',
                'button:has-text("People")',
            ]
            
            for selector in badge_selectors:
                try:
                    badge = await page.query_selector(selector)
                    if badge:
                        # Get aria-label or text content
                        aria_label = await badge.get_attribute("aria-label") or ""
                        badge_text = await badge.inner_text() or ""
                        
                        # Extract number from text (e.g., "People (2)" or just "2")
                        import re
                        all_text = f"{aria_label} {badge_text}"
                        matches = re.findall(r'\d+', all_text)
                        
                        if matches:
                            count = int(matches[0])
                            return count
                except Exception:
                    continue
            
            # Alternative: Look for badge number in the button (Google Meet shows "1" badge)
            try:
                people_button = await page.query_selector('button[aria-label*="People" i]')
                if people_button:
                    # Look for number badge inside or next to button
                    badge_number = await people_button.query_selector('span, div')
                    if badge_number:
                        badge_text = await badge_number.inner_text()
                        import re
                        match = re.search(r'\d+', badge_text)
                        if match:
                            return int(match.group())
                    
                    # Also check the button's text directly
                    button_text = await people_button.inner_text()
                    import re
                    match = re.search(r'\d+', button_text)
                    if match:
                        return int(match.group())
            except Exception:
                pass
                
        except Exception as e:
            logger.debug(f"Could not get badge count: {e}")
        
        return 0
    
    async def _check_teams_empty(self, page: Page) -> bool:
        """Check if Teams meeting is empty (only bot/user)."""
        try:
            # Teams shows "You're the only one" or similar
            content = (await page.content()).lower()
            empty_indicators = [
                "you're the only one",
                "you are the only one",
                "waiting for others",
                "no one else is here",
            ]
            
            for indicator in empty_indicators:
                if indicator in content:
                    return True
            
            # Check participant count in Teams
            try:
                # Open participants panel
                participants_button = await page.query_selector(
                    '[aria-label*="Participants"], [data-tid="participant-button"]'
                )
                if participants_button:
                    await participants_button.click()
                    await page.wait_for_timeout(1500)
                
                # Count participants
                participant_items = await page.query_selector_all(
                    '[data-tid="participant-list-item"]'
                )
                
                # Filter valid participants (exclude empty/header elements)
                valid_count = 0
                for item in participant_items:
                    try:
                        name = await item.query_selector('[data-tid="participant-name"]')
                        if name:
                            name_text = await name.inner_text()
                            if name_text and name_text.strip():
                                valid_count += 1
                    except Exception:
                        continue
                
                # If only 1 participant (the bot/user), meeting is empty
                if valid_count == 1:
                    logger.info(
                        "Only bot/user detected in Teams meeting",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "participant_count": valid_count,
                            }
                        },
                    )
                    return True
            
            except Exception as e:
                logger.debug(f"Error checking Teams participant count: {e}")
        
        except Exception as e:
            logger.debug(f"Error in Teams empty meeting check: {e}")
        
        return False
    
    async def _check_generic_empty(self, page: Page) -> bool:
        """Generic empty meeting check."""
        try:
            content = (await page.content()).lower()
            return any(indicator in content for indicator in [
                "you're the only one",
                "waiting for others",
                "no one else",
            ])
        except Exception:
            return False
    
    async def leave_meeting_cleanly(self, page: Page) -> None:
        """Leave the meeting cleanly using UI button if available."""
        logger.info(
            "Leaving meeting cleanly",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                }
            },
        )
        
        try:
            if self.platform == "gmeet":
                await self._leave_gmeet_meeting(page)
            elif self.platform == "teams":
                await self._leave_teams_meeting(page)
            else:
                # Generic leave attempt
                await self._leave_generic_meeting(page)
        except Exception as e:
            logger.warning(
                f"Could not leave meeting via UI button: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
            # Continue anyway - context will close
    
    async def _leave_gmeet_meeting(self, page: Page) -> None:
        """Leave Google Meet meeting using leave button."""
        leave_selectors = [
            '[aria-label*="Leave call" i]',
            '[aria-label*="Leave meeting" i]',
            'button[jsname="CQylAd"]',  # Common leave button
            '[data-tooltip*="Leave" i]',
        ]
        
        for selector in leave_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click(timeout=3000)
                    await page.wait_for_timeout(2000)
                    logger.debug("Clicked leave button in Google Meet")
                    return
            except Exception:
                continue
    
    async def _leave_teams_meeting(self, page: Page) -> None:
        """Leave Teams meeting using leave button."""
        leave_selectors = [
            '[aria-label*="Leave" i]',
            '[data-tid="leave-button"]',
            'button[title*="Leave" i]',
        ]
        
        for selector in leave_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click(timeout=3000)
                    await page.wait_for_timeout(2000)
                    logger.debug("Clicked leave button in Teams")
                    return
            except Exception:
                continue
    
    async def _leave_generic_meeting(self, page: Page) -> None:
        """Generic leave attempt."""
        leave_selectors = [
            'button[aria-label*="Leave" i]',
            'button[aria-label*="Exit" i]',
            '[class*="leave" i]',
        ]
        
        for selector in leave_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click(timeout=3000)
                    return
            except Exception:
                continue
    
    async def _capture_screenshot(self, page: Page, reason: str) -> Optional[str]:
        """Capture screenshot for debugging."""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"end_{self.session_id}_{reason}_{timestamp}.png"
            filepath = self.data_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=True)
            
            logger.info(
                f"Screenshot captured: {filename}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "screenshot": filename,
                        "reason": reason,
                    }
                },
            )
            
            return str(filepath.relative_to(self.data_dir))
        
        except Exception as e:
            logger.warning(
                f"Could not capture screenshot: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
            return None

