"""
ROBUST participant extraction for Google Meet - uses multiple methods and JavaScript evaluation.

This is a more reliable extraction that doesn't filter too aggressively.
"""
from typing import List, Dict, Set
from playwright.async_api import Page

from .logging_utils import get_logger

logger = get_logger(__name__)


class RobustParticipantExtractor:
    """Robust participant extraction using multiple methods."""
    
    async def extract_participants(self, page: Page) -> List[Dict]:
        """
        Extract participants using multiple robust methods.
        
        Returns ALL participants found, including bot/user.
        CRITICAL: If participant badge shows count > 0 but we find 0, we're missing participants!
        """
        all_participants = []
        seen_names: Set[str] = set()
        
        # CRITICAL: First check participant badge count (shows actual count)
        badge_count = await self._get_participant_badge_count(page)
        
        # Method 1: DOM selectors (data-self-name) - most reliable, try first
        dom_participants = await self._extract_via_dom_selectors(page)
        for p in dom_participants:
            name = p.get("name", "").strip()
            if name and name.lower() not in seen_names:
                all_participants.append(p)
                seen_names.add(name.lower())
        
        # Method 2: People panel text extraction
        panel_participants = await self._extract_via_panel_text(page)
        for p in panel_participants:
            name = p.get("name", "").strip()
            if name and name.lower() not in seen_names:
                all_participants.append(p)
                seen_names.add(name.lower())
        
        # Method 3: JavaScript evaluation (fallback if others fail)
        if len(all_participants) == 0 or (badge_count and badge_count > len(all_participants)):
            try:
                js_participants = await self._extract_via_javascript(page)
                for p in js_participants:
                    name = p.get("name", "").strip()
                    if name and name.lower() not in seen_names:
                        all_participants.append(p)
                        seen_names.add(name.lower())
            except Exception as e:
                logger.warning(f"JavaScript extraction failed (non-critical): {e}")
        
        # CRITICAL CHECK: If badge shows participants but we found none, something is wrong!
        if badge_count and badge_count > 0 and len(all_participants) == 0:
            logger.error(
                f"CRITICAL: Participant badge shows {badge_count} but extraction found 0! Using badge count as fallback.",
                extra={
                    "extra_data": {
                        "badge_count": badge_count,
                        "extracted_count": len(all_participants),
                        "warning": "extraction_failed_using_badge_count",
                    }
                },
            )
            # If badge shows participants but we can't extract names, create placeholder entries
            # This prevents false "empty meeting" detection
            for i in range(badge_count):
                all_participants.append({
                    "name": f"Participant {i+1}",
                    "role": "guest",
                    "is_speaking": False,
                    "source": "badge_count_fallback",
                })
        
        logger.info(
            f"ROBUST EXTRACTION: Found {len(all_participants)} total participants (badge shows {badge_count})",
            extra={
                "extra_data": {
                    "total_participants": len(all_participants),
                    "badge_count": badge_count,
                    "participant_names": [p.get("name") for p in all_participants],
                    "dom_count": len(dom_participants),
                    "panel_count": len(panel_participants),
                }
            },
        )
        
        return all_participants
    
    async def _get_participant_badge_count(self, page: Page) -> int:
        """
        Get participant count from the badge/button.
        
        This is CRITICAL - the badge shows the actual count even if extraction fails.
        Based on screenshot: Badge shows "1" in a small circle above the People icon.
        """
        try:
            # Use JavaScript to find badge count (most reliable)
            badge_count = await page.evaluate("""
            (() => {
                // Look for People button with badge
                const peopleButton = Array.from(document.querySelectorAll('button')).find(btn => {
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    return ariaLabel.includes('people') || ariaLabel.includes('show everyone');
                });
                
                if (peopleButton) {
                    // Look for badge number near the button
                    const parent = peopleButton.parentElement;
                    if (parent) {
                        // Check for badge spans/divs with numbers
                        const badges = parent.querySelectorAll('span, div');
                        for (let badge of badges) {
                            const text = badge.textContent || badge.innerText || '';
                            const match = text.match(/^\\d+$/);
                            if (match) {
                                return parseInt(match[0]);
                            }
                        }
                    }
                    
                    // Check aria-label for count
                    const ariaLabel = peopleButton.getAttribute('aria-label') || '';
                    const match = ariaLabel.match(/\\d+/);
                    if (match) {
                        return parseInt(match[0]);
                    }
                }
                
                // Alternative: Look for badge with number "1"
                const badge = document.querySelector('[role="button"] span:has-text("1"), [role="button"] div:has-text("1")');
                if (badge) {
                    const text = badge.textContent || badge.innerText || '';
                    const match = text.match(/^\\d+$/);
                    if (match) {
                        return parseInt(match[0]);
                    }
                }
                
                return 0;
            })()
            """)
            
            if badge_count and badge_count > 0:
                logger.info(f"Participant badge shows {badge_count} participants")
                return badge_count
            
            # Fallback: Try multiple selectors for participant badge
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
                            logger.info(f"Participant badge shows {count} participants (via selector)")
                            return count
                except Exception:
                    continue
                
        except Exception as e:
            logger.debug(f"Could not get badge count: {e}")
        
        return 0
    
    async def _extract_via_javascript(self, page: Page) -> List[Dict]:
        """Extract participants using JavaScript evaluation - most reliable."""
        participants = []
        
        try:
            # Ensure People panel is open
            await self._ensure_people_panel_open(page)
            await page.wait_for_timeout(3000)  # Wait longer for panel to fully load
            
            # Use comprehensive JavaScript to extract participants from Contributors section
            js_code = """
            (() => {
                const participants = [];
                const seen = new Set();
                
                try {
                    // Method 1: Find Contributors section (most reliable based on screenshot)
                    const contributorsSection = Array.from(document.querySelectorAll('div, section')).find(el => {
                        const text = (el.textContent || '').toUpperCase();
                        return text.includes('CONTRIBUTORS') || text.includes('IN THE MEETING');
                    });
                    
                    if (contributorsSection) {
                        const listItems = contributorsSection.querySelectorAll('[role="listitem"]');
                        for (let i = 0; i < listItems.length; i++) {
                            const item = listItems[i];
                            const text = item.innerText || item.textContent || '';
                            if (!text || text.trim().length < 2) continue;
                            
                            // Get full text to check for (You)
                            let fullName = '';
                            
                            // Try data-self-name first
                            const nameEl = item.querySelector('[data-self-name]');
                            if (nameEl) {
                                fullName = nameEl.getAttribute('data-self-name') || '';
                            }
                            
                            // If no data-self-name, try getting text from name span
                            if (!fullName) {
                                const nameSpan = item.querySelector('span[dir="auto"]') || item.querySelector('div[dir="auto"]');
                                if (nameSpan) {
                                    fullName = nameSpan.innerText || nameSpan.textContent || '';
                                }
                            }
                            
                            // Fallback: get first line of text
                            if (!fullName) {
                                const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                                if (lines.length > 0) {
                                    fullName = lines[0];
                                }
                            }
                            
                            if (fullName && fullName.trim()) {
                                const originalName = fullName.trim();
                                let cleanName = originalName;
                                let isBot = false;
                                
                                // Check for (You) suffix - case insensitive
                                const youPattern = /\\s*\\(you\\)$/i;
                                if (youPattern.test(cleanName)) {
                                    cleanName = cleanName.replace(youPattern, '').trim();
                                    isBot = true;
                                }
                                
                                if (cleanName && cleanName.length > 1) {
                                    const nameLower = cleanName.toLowerCase();
                                    if (!seen.has(nameLower)) {
                                        seen.add(nameLower);
                                        participants.push({
                                            name: cleanName,
                                            originalName: originalName,
                                            isBot: isBot,
                                            source: 'contributors-section'
                                        });
                                    }
                                }
                            }
                        }
                    }
                    
                    // Method 2: Find all elements with data-self-name (fallback)
                    if (participants.length === 0) {
                        const elementsWithName = document.querySelectorAll('[data-self-name]');
                        for (let i = 0; i < elementsWithName.length; i++) {
                            const el = elementsWithName[i];
                            const name = el.getAttribute('data-self-name');
                            if (name && name.trim()) {
                                const listItem = el.closest('[role="listitem"]');
                                if (listItem) {
                                    const originalName = name.trim();
                                    let cleanName = originalName;
                                    let isBot = false;
                                    const youPattern = /\\s*\\(you\\)$/i;
                                    if (youPattern.test(cleanName)) {
                                        cleanName = cleanName.replace(youPattern, '').trim();
                                        isBot = true;
                                    }
                                    const nameLower = cleanName.toLowerCase();
                                    if (!seen.has(nameLower)) {
                                        seen.add(nameLower);
                                        participants.push({
                                            name: cleanName,
                                            originalName: originalName,
                                            isBot: isBot,
                                            source: 'data-self-name'
                                        });
                                    }
                                }
                            }
                        }
                    }
                    
                    // Method 3: Find participant list items in People panel (last resort)
                    if (participants.length === 0) {
                        const listItems = document.querySelectorAll('[role="listitem"]');
                        for (let i = 0; i < listItems.length; i++) {
                            const item = listItems[i];
                            const text = item.innerText || item.textContent || '';
                            if (!text || text.trim().length < 2) continue;
                            
                            const textLower = text.toLowerCase();
                            const uiIndicators = ['backgrounds and effects', 'your microphone is off', 'your camera is off', 'settings', 'more options', 'add people', 'search for people'];
                            let isUI = false;
                            for (let j = 0; j < uiIndicators.length; j++) {
                                if (textLower.includes(uiIndicators[j])) {
                                    isUI = true;
                                    break;
                                }
                            }
                            
                            if (!isUI) {
                                const nameEl = item.querySelector('[data-self-name]') || item.querySelector('span[dir="auto"]') || item.querySelector('div[dir="auto"]');
                                if (nameEl) {
                                    let name = nameEl.getAttribute('data-self-name') || nameEl.innerText || nameEl.textContent || '';
                                    if (!name) {
                                        name = text.split('\\n')[0].trim();
                                    }
                                    
                                    if (name && name.trim() && name.trim().length > 1) {
                                        const originalName = name.trim();
                                        let cleanName = originalName;
                                        let isBot = false;
                                        const youPattern = /\\s*\\(you\\)$/i;
                                        if (youPattern.test(cleanName)) {
                                            cleanName = cleanName.replace(youPattern, '').trim();
                                            isBot = true;
                                        }
                                        if (cleanName && cleanName.length > 1) {
                                            const nameLower = cleanName.toLowerCase();
                                            if (!seen.has(nameLower)) {
                                                seen.add(nameLower);
                                                participants.push({
                                                    name: cleanName,
                                                    originalName: originalName,
                                                    isBot: isBot,
                                                    source: 'listitem-text'
                                                });
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.error('JS extraction error:', e);
                }
                
                return participants;
            })()
            """
            
            result = await page.evaluate(js_code)
            
            for item in result:
                name = item.get("name", "")
                original_name = item.get("originalName", name)
                is_bot = item.get("isBot", False)
                
                # CRITICAL: Log extraction details
                logger.info(
                    f"Extracted participant: name='{name}', original='{original_name}', is_bot={is_bot}",
                    extra={
                        "extra_data": {
                            "name": name,
                            "original_name": original_name,
                            "is_bot": is_bot,
                            "source": item.get("source", "unknown"),
                        }
                    },
                )
                
                participants.append({
                    "name": name,
                    "role": "guest",
                    "is_speaking": False,
                    "is_bot": is_bot,
                    "original_name": original_name,
                })
            
            logger.info(f"JavaScript extraction found {len(participants)} participants")
            
        except Exception as e:
            logger.warning(f"JavaScript extraction failed: {e}", exc_info=True)
        
        return participants
    
    async def _extract_via_dom_selectors(self, page: Page) -> List[Dict]:
        """Extract using DOM selectors."""
        participants = []
        
        try:
            # Find all elements with data-self-name
            elements = await page.query_selector_all('[data-self-name]')
            
            for element in elements:
                try:
                    name = await element.get_attribute("data-self-name")
                    if not name or not name.strip():
                        continue
                    
                    # Check if it's in a list item
                    is_in_listitem = await element.evaluate("""
                        el => {
                            const listItem = el.closest('[role="listitem"]');
                            return listItem !== null;
                        }
                    """)
                    
                    if is_in_listitem:
                        # Preserve original name to detect bot
                        original_name = name.strip()
                        clean_name = original_name
                        is_bot = False
                        # Case-insensitive check for (You) suffix
                        import re
                        you_pattern = re.compile(r'\s*\(you\)$', re.IGNORECASE)
                        if you_pattern.search(clean_name):
                            clean_name = you_pattern.sub('', clean_name).strip()
                            is_bot = True
                        
                        if clean_name and len(clean_name) > 1:
                            participants.append({
                                "name": clean_name,
                                "role": "guest",
                                "is_speaking": False,
                                "is_bot": is_bot,
                                "original_name": original_name,
                            })
                            logger.info(f"DOM extractor: name='{clean_name}', original='{original_name}', is_bot={is_bot}")
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"DOM selector extraction failed: {e}")
        
        return participants
    
    async def _extract_via_panel_text(self, page: Page) -> List[Dict]:
        """Extract by reading People panel text - with better error handling."""
        participants = []
        seen_names = set()
        
        try:
            # Ensure panel is open
            await self._ensure_people_panel_open(page)
            await page.wait_for_timeout(2000)  # Wait longer for panel to load
            
            # Try to find People panel container
            panel_selectors = [
                '[aria-label*="People" i][role="dialog"]',
                '[aria-label*="Show everyone" i]',
                '[role="dialog"][aria-label*="People" i]',
            ]
            
            panel = None
            for selector in panel_selectors:
                try:
                    panel = await page.query_selector(selector)
                    if panel:
                        break
                except Exception:
                    continue
            
            if not panel:
                # If panel not found, try to get list items from entire page
                list_items = await page.query_selector_all('[role="listitem"]')
            else:
                # Get list items within panel
                list_items = await panel.query_selector_all('[role="listitem"]')
            
            logger.debug(f"Found {len(list_items)} list items to check")
            
            for item in list_items:
                try:
                    # Get text content
                    text = await item.inner_text()
                    if not text or len(text.strip()) < 2:
                        continue
                    
                    text_lower = text.lower()
                    
                    # Skip obvious UI elements
                    ui_indicators = [
                        "backgrounds and effects",
                        "your microphone is off",
                        "your camera is off",
                        "you can't unmute",
                        "settings",
                        "more options",
                        "turn on",
                        "turn off",
                    ]
                    
                    if any(indicator in text_lower for indicator in ui_indicators):
                        continue
                    
                    # Try multiple ways to get the name
                    name = None
                    
                    # Method 1: data-self-name attribute
                    name_el = await item.query_selector('[data-self-name]')
                    if name_el:
                        name = await name_el.get_attribute("data-self-name")
                    
                    # Method 2: span with dir="auto"
                    if not name:
                        name_el = await item.query_selector('span[dir="auto"]')
                        if name_el:
                            name = await name_el.inner_text()
                    
                    # Method 3: aria-label
                    if not name:
                        name_el = await item.query_selector('[aria-label]')
                        if name_el:
                            name = await name_el.get_attribute("aria-label")
                    
                    # Method 4: First line of text (fallback)
                    if not name:
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        if lines:
                            # Use first line if it looks like a name
                            first_line = lines[0]
                            if len(first_line) > 1 and len(first_line) < 100:
                                # Not a sentence (no period or short)
                                if '.' not in first_line or len(first_line.split('.')) <= 2:
                                    name = first_line
                    
                    if name and name.strip():
                        original_name = name.strip()
                        clean_name = original_name
                        is_bot = False
                        # Case-insensitive check for (You) suffix
                        import re
                        you_pattern = re.compile(r'\s*\(you\)$', re.IGNORECASE)
                        if you_pattern.search(clean_name):
                            clean_name = you_pattern.sub('', clean_name).strip()
                            is_bot = True
                        
                        if clean_name and len(clean_name) > 1:
                            name_lower = clean_name.lower()
                            if name_lower not in seen_names:
                                seen_names.add(name_lower)
                                participants.append({
                                    "name": clean_name,
                                    "role": "guest",
                                    "is_speaking": False,
                                    "is_bot": is_bot,
                                    "original_name": original_name,
                                })
                                logger.info(f"Panel extractor: name='{clean_name}', original='{original_name}', is_bot={is_bot}")
                except Exception as e:
                    logger.debug(f"Error processing list item: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Panel text extraction failed: {e}")
        
        return participants
    
    async def _ensure_people_panel_open(self, page: Page) -> None:
        """Ensure People panel is open."""
        try:
            # Check if panel is already open
            panel_open = await page.query_selector('[aria-label*="People" i][role="dialog"]:visible, [aria-label*="Show everyone" i]:visible')
            if panel_open:
                return
            
            # Try to open People panel
            selectors = [
                '[aria-label*="Show everyone" i]',
                '[aria-label*="People" i]',
                'button[aria-label*="People" i]',
                'button[data-tooltip*="People" i]',
            ]
            
            for selector in selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        await button.click()
                        await page.wait_for_timeout(1000)
                        return
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Could not open People panel: {e}")

