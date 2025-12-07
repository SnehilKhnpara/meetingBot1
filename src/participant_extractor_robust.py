"""
ROBUST participant extraction for Google Meet - uses multiple methods and JavaScript evaluation.

This version properly extracts REAL participants and filters out ALL UI elements.
ENHANCED: Better bot/self detection for Google profile login scenarios.

CRITICAL: Google Meet shows participants in the "Contributors" section of the People panel.
Each participant is in a [role="listitem"] with a [data-self-name] attribute containing the name.
"""
from typing import List, Dict, Set, Optional
import re
from playwright.async_api import Page

from .logging_utils import get_logger
from .participant_name_filter import is_valid_participant_name, clean_participant_name

logger = get_logger(__name__)


# Extended blacklist for UI elements that should NEVER be treated as participants
UI_ELEMENT_BLACKLIST = [
    # Settings and effects
    "backgrounds and effects",
    "visual effects",
    "apply visual effects",
    "background blur",
    
    # Microphone/camera notifications
    "your microphone is off",
    "your camera is off",
    "microphone is off",
    "camera is off",
    "microphone is on",
    "camera is on",
    
    # Remote mute/unmute notifications
    "you can't remotely mute",
    "you can't unmute someone else",
    "can't remotely mute",
    "can't unmute",
    
    # Meeting controls
    "turn on microphone",
    "turn off microphone",
    "turn on camera",
    "turn off camera",
    "mute microphone",
    "unmute microphone",
    "present now",
    "stop presenting",
    "raise hand",
    "lower hand",
    "end call",
    "leave call",
    
    # Panel headers and sections
    "in the meeting",
    "contributors",
    "add people",
    "search for people",
    "invite",
    "share",
    "host controls",
    "meeting details",
    "other people",
    "in this call",
    
    # Waiting/connection states
    "waiting for others",
    "you're the only one",
    "connecting",
    "reconnecting",
    "joining",
    
    # General UI text
    "settings",
    "options",
    "more options",
    "more actions",
    "send a message",
    "chat",
    "activities",
    "captions",
    "subtitles",
    "recording",
    "breakout rooms",
    "layout",
    "tiled",
    "spotlight",
    "sidebar",
    "auto",
    
    # Permissions
    "allow",
    "deny",
    "grant",
    "permission",
    "access",
    "enable",
    "disable",
]


def is_ui_element(text: str) -> bool:
    """
    CRITICAL: Check if text is a UI element, not a real participant name.
    
    This is the PRIMARY filter - if this returns True, the text is NOT a participant.
    """
    if not text or not isinstance(text, str):
        return True
    
    text_lower = text.strip().lower()
    
    if not text_lower:
        return True
    
    # Check against extended blacklist (case-insensitive)
    for blacklisted in UI_ELEMENT_BLACKLIST:
        if blacklisted in text_lower:
            return True
    
    # Additional pattern checks
    
    # Starts with "your" or "you" (notifications)
    if text_lower.startswith("your ") or text_lower.startswith("you "):
        return True
    
    # Contains "can't" or "cannot" (error messages)
    if "can't" in text_lower or "cannot" in text_lower:
        return True
    
    # Ends with period and is long (likely a notification message)
    if text_lower.endswith(".") and len(text_lower.split()) > 4:
        return True
    
    # Contains multiple sentences (notifications)
    sentences = [s for s in text_lower.split(".") if s.strip()]
    if len(sentences) > 2:
        return True
    
    # Too short (single letter, etc.)
    if len(text_lower) < 2:
        return True
    
    # Too long for a name (likely a message)
    if len(text) > 100:
        return True
    
    # Must contain at least one letter
    if not any(c.isalpha() for c in text):
        return True
    
    # All caps and contains numbers (likely system text)
    if text.isupper() and any(c.isdigit() for c in text):
        return True
    
    return False


class RobustParticipantExtractor:
    """Robust participant extraction using multiple methods with proper filtering."""
    
    def __init__(self):
        self._detected_bot_name: Optional[str] = None
    
    async def extract_participants(self, page: Page) -> List[Dict]:
        """
        Extract participants using multiple robust methods.
        
        Returns ALL valid participants found, including bot/user.
        CRITICAL: Uses proper filtering to exclude UI elements.
        ENHANCED: Better "(You)" and self-indicator detection.
        """
        all_participants = []
        seen_names: Set[str] = set()
        
        logger.info("Starting ROBUST participant extraction with enhanced bot detection")
        
        # CRITICAL: First check participant badge count (shows actual count)
        badge_count = await self._get_participant_badge_count(page)
        logger.info(f"Participant badge count: {badge_count}")
        
        # Ensure People panel is open before extraction
        await self._ensure_people_panel_open(page)
        await page.wait_for_timeout(2000)  # Wait for panel to fully load
        
        # Method 1: JavaScript-based extraction (most reliable for Google Meet)
        # This directly queries the DOM structure of Google Meet
        js_participants = await self._extract_via_javascript(page)
        for p in js_participants:
            name = p.get("name", "").strip()
            if name and name.lower() not in seen_names:
                # Double-check with our filter
                if not is_ui_element(name):
                    all_participants.append(p)
                    seen_names.add(name.lower())
                    
                    # Track detected bot name
                    if p.get("is_bot", False) and not self._detected_bot_name:
                        self._detected_bot_name = name
                        logger.info(f"Detected bot name: {name}")
                    
                    logger.debug(f"JS extraction: Added valid participant '{name}' (is_bot: {p.get('is_bot', False)})")
                else:
                    logger.debug(f"JS extraction: Filtered out UI element '{name}'")
        
        # Method 2: DOM selectors (data-self-name) - backup
        if len(all_participants) < badge_count:
            dom_participants = await self._extract_via_dom_selectors(page)
            for p in dom_participants:
                name = p.get("name", "").strip()
                if name and name.lower() not in seen_names:
                    if not is_ui_element(name):
                        all_participants.append(p)
                        seen_names.add(name.lower())
                        
                        if p.get("is_bot", False) and not self._detected_bot_name:
                            self._detected_bot_name = name
                        
                        logger.debug(f"DOM extraction: Added valid participant '{name}'")
                    else:
                        logger.debug(f"DOM extraction: Filtered out UI element '{name}'")
        
        # Method 3: Panel text extraction - last resort
        if len(all_participants) < badge_count:
            panel_participants = await self._extract_via_panel_text(page)
            for p in panel_participants:
                name = p.get("name", "").strip()
                if name and name.lower() not in seen_names:
                    if not is_ui_element(name):
                        all_participants.append(p)
                        seen_names.add(name.lower())
                        
                        if p.get("is_bot", False) and not self._detected_bot_name:
                            self._detected_bot_name = name
                        
                        logger.debug(f"Panel extraction: Added valid participant '{name}'")
                    else:
                        logger.debug(f"Panel extraction: Filtered out UI element '{name}'")
        
        # CRITICAL: If we extracted fewer than badge count, don't false-positive empty meeting
        if len(all_participants) == 0 and badge_count > 0:
            logger.warning(
                f"EXTRACTION WARNING: Badge shows {badge_count} but extracted 0 participants - using fallback",
                extra={
                    "extra_data": {
                        "badge_count": badge_count,
                        "extracted_count": 0,
                        "warning": "extraction_failed_using_badge_count",
                    }
                },
            )
            # Create placeholder entries to prevent false "empty meeting" detection
            for i in range(badge_count):
                all_participants.append({
                    "name": f"Participant {i+1}",
                    "role": "guest",
                    "is_speaking": False,
                    "is_bot": False,
                    "source": "badge_count_fallback",
                })
        
        logger.info(
            f"ROBUST EXTRACTION COMPLETE: Found {len(all_participants)} valid participants (badge shows {badge_count})",
            extra={
                "extra_data": {
                    "total_participants": len(all_participants),
                    "badge_count": badge_count,
                    "participant_names": [p.get("name") for p in all_participants],
                    "detected_bot_name": self._detected_bot_name,
                }
            },
        )
        
        return all_participants
    
    def get_detected_bot_name(self) -> Optional[str]:
        """Return the detected bot name (the participant with '(You)' suffix)."""
        return self._detected_bot_name
    
    async def _get_participant_badge_count(self, page: Page) -> int:
        """
        Get participant count from the badge/button.
        
        This is CRITICAL - the badge shows the actual count even if extraction fails.
        """
        try:
            # Use JavaScript to find badge count (most reliable)
            badge_count = await page.evaluate("""
            (() => {
                try {
                    // Method 1: Look for People button with badge number
                    const buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                        if (ariaLabel.includes('people') || ariaLabel.includes('show everyone') || ariaLabel.includes('participant')) {
                            // Check for badge number in button content
                            const spans = btn.querySelectorAll('span, div');
                            for (let span of spans) {
                                const text = (span.textContent || '').trim();
                                if (/^\\d+$/.test(text)) {
                                    return parseInt(text);
                                }
                            }
                            // Check aria-label for number
                            const match = ariaLabel.match(/(\\d+)/);
                            if (match) {
                                return parseInt(match[1]);
                            }
                        }
                    }
                    
                    // Method 2: Look for any element with participant count
                    const countElements = document.querySelectorAll('[data-participant-count]');
                    for (let el of countElements) {
                        const count = el.getAttribute('data-participant-count');
                        if (count) {
                            return parseInt(count);
                        }
                    }
                    
                    // Method 3: Look for "X in call" or similar text
                    const allText = document.body.innerText || '';
                    const inCallMatch = allText.match(/(\\d+)\\s*(?:in\\s*(?:the\\s*)?(?:call|meeting))/i);
                    if (inCallMatch) {
                        return parseInt(inCallMatch[1]);
                    }
                    
                } catch (e) {
                    console.error('Badge count error:', e);
                }
                return 0;
            })()
            """)
            
            if badge_count and badge_count > 0:
                return badge_count
                
        except Exception as e:
            logger.debug(f"Could not get badge count: {e}")
        
        return 0
    
    async def _extract_via_javascript(self, page: Page) -> List[Dict]:
        """
        Extract participants using JavaScript evaluation - most reliable for Google Meet.
        
        CRITICAL: This targets the SPECIFIC DOM structure of Google Meet's People panel.
        ENHANCED: Better detection of "(You)" suffix and self-indicators.
        """
        participants = []
        
        try:
            # Comprehensive JavaScript to extract real participants with enhanced bot detection
            js_code = """
            (() => {
                const participants = [];
                const seen = new Set();
                
                // Extended UI element blacklist
                const uiBlacklist = [
                    'backgrounds and effects', 'visual effects', 'your microphone is off',
                    'your camera is off', 'microphone is off', 'camera is off',
                    'you can\\'t remotely mute', 'you can\\'t unmute someone else',
                    'can\\'t remotely mute', 'can\\'t unmute', 'turn on microphone',
                    'turn off microphone', 'turn on camera', 'turn off camera',
                    'mute microphone', 'unmute microphone', 'present now',
                    'settings', 'options', 'more options', 'add people',
                    'search for people', 'in the meeting', 'contributors',
                    'waiting for others', 'you\\'re the only one', 'connecting',
                    'joining', 'host controls', 'meeting details'
                ];
                
                function isUIElement(text) {
                    if (!text || text.length < 2) return true;
                    const lower = text.toLowerCase().trim();
                    
                    // Check blacklist
                    for (let item of uiBlacklist) {
                        if (lower.includes(item)) return true;
                    }
                    
                    // Starts with "your" or "you " (notifications)
                    if (lower.startsWith('your ') || lower.startsWith('you ')) return true;
                    
                    // Contains can't/cannot (error messages)
                    if (lower.includes("can't") || lower.includes('cannot')) return true;
                    
                    // Ends with period and is a sentence
                    if (lower.endsWith('.') && lower.split(' ').length > 4) return true;
                    
                    return false;
                }
                
                // ENHANCED: Check multiple indicators for "self" participant (the bot)
                function checkIfSelf(element, name) {
                    // Check 1: "(You)" suffix in name (case-insensitive)
                    if (/\\(you\\)/i.test(name)) {
                        return true;
                    }
                    
                    // Check 2: Element has specific self-indicator classes
                    const classList = Array.from(element.classList || []).join(' ').toLowerCase();
                    if (classList.includes('self') || classList.includes('local') || classList.includes('me')) {
                        return true;
                    }
                    
                    // Check 3: Look for "You" label inside the element
                    const youLabels = element.querySelectorAll('[data-self-name*="(You)"], [data-self-name*="(you)"]');
                    if (youLabels.length > 0) {
                        return true;
                    }
                    
                    // Check 4: Check for aria-label containing "you"
                    const ariaLabel = (element.getAttribute('aria-label') || '').toLowerCase();
                    if (ariaLabel.includes('(you)') || ariaLabel === 'you') {
                        return true;
                    }
                    
                    // Check 5: Check for mute/unmute controls specific to self
                    // Self participants often have "Mute microphone" instead of "Mute [Name]"
                    const muteBtn = element.querySelector('[aria-label*="Mute microphone" i], [aria-label*="Turn off microphone" i]');
                    if (muteBtn) {
                        return true;
                    }
                    
                    // Check 6: Look for pin/unpin self button
                    const pinSelfBtn = element.querySelector('[aria-label*="Pin yourself" i], [aria-label*="Unpin yourself" i]');
                    if (pinSelfBtn) {
                        return true;
                    }
                    
                    // Check 7: Look for text content indicating self
                    const innerText = (element.innerText || '').toLowerCase();
                    if (innerText.includes('(you)')) {
                        return true;
                    }
                    
                    return false;
                }
                
                function extractName(element) {
                    // Method 1: data-self-name attribute (most reliable)
                    const selfNameEl = element.querySelector('[data-self-name]');
                    if (selfNameEl) {
                        return selfNameEl.getAttribute('data-self-name');
                    }
                    
                    // Method 2: Look for span with dir="auto" containing the name
                    const spans = element.querySelectorAll('span[dir="auto"], div[dir="auto"]');
                    for (let span of spans) {
                        const text = (span.textContent || '').trim();
                        if (text && text.length > 1 && text.length < 100 && !isUIElement(text)) {
                            return text;
                        }
                    }
                    
                    // Method 3: First line of text (careful filtering)
                    const fullText = element.innerText || '';
                    const lines = fullText.split('\\n').map(l => l.trim()).filter(l => l.length > 1);
                    for (let line of lines) {
                        if (!isUIElement(line) && line.length < 100) {
                            return line;
                        }
                    }
                    
                    return null;
                }
                
                try {
                    // Strategy 1: Find Contributors section and get list items
                    const listItems = document.querySelectorAll('[role="listitem"]');
                    
                    for (let item of listItems) {
                        const name = extractName(item);
                        if (name && !isUIElement(name)) {
                            const nameLower = name.toLowerCase().replace(/\\s*\\(you\\)$/i, '').trim().toLowerCase();
                            
                            if (!seen.has(nameLower)) {
                                seen.add(nameLower);
                                
                                // ENHANCED: Use multiple methods to detect if this is the bot
                                let isBot = checkIfSelf(item, name);
                                
                                // Clean the name - remove (You) suffix
                                let cleanName = name.trim();
                                const youPattern = /\\s*\\(you\\)$/i;
                                if (youPattern.test(cleanName)) {
                                    cleanName = cleanName.replace(youPattern, '').trim();
                                    isBot = true;  // Definitely the bot if has (You)
                                }
                                
                                if (cleanName.length > 1) {
                                    participants.push({
                                        name: cleanName,
                                        originalName: name,
                                        isBot: isBot,
                                        source: 'listitem'
                                    });
                                }
                            }
                        }
                    }
                    
                    // Strategy 2: Direct data-self-name search (backup)
                    if (participants.length === 0) {
                        const nameElements = document.querySelectorAll('[data-self-name]');
                        for (let el of nameElements) {
                            const name = el.getAttribute('data-self-name');
                            if (name && !isUIElement(name)) {
                                const listItem = el.closest('[role="listitem"]');
                                if (listItem) {
                                    const nameLower = name.toLowerCase().replace(/\\s*\\(you\\)$/i, '').trim().toLowerCase();
                                    
                                    if (!seen.has(nameLower)) {
                                        seen.add(nameLower);
                                        
                                        let isBot = checkIfSelf(listItem, name);
                                        
                                        let cleanName = name.trim();
                                        const youPattern = /\\s*\\(you\\)$/i;
                                        if (youPattern.test(cleanName)) {
                                            cleanName = cleanName.replace(youPattern, '').trim();
                                            isBot = true;
                                        }
                                        
                                        if (cleanName.length > 1) {
                                            participants.push({
                                                name: cleanName,
                                                originalName: name,
                                                isBot: isBot,
                                                source: 'data-self-name'
                                            });
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
                source = item.get("source", "unknown")
                
                # Final validation with our Python filter
                if name and not is_ui_element(name):
                    logger.info(f"JS extracted: '{name}' (original: '{original_name}', is_bot: {is_bot}, source: {source})")
                    participants.append({
                        "name": name,
                        "role": "guest",
                        "is_speaking": False,
                        "is_bot": is_bot,
                        "original_name": original_name,
                    })
                else:
                    logger.debug(f"JS filtered: '{name}' (failed Python validation)")
            
        except Exception as e:
            logger.warning(f"JavaScript extraction failed: {e}", exc_info=True)
        
        return participants
    
    async def _extract_via_dom_selectors(self, page: Page) -> List[Dict]:
        """Extract using DOM selectors - backup method with enhanced bot detection."""
        participants = []
        
        try:
            # Find all elements with data-self-name attribute
            elements = await page.query_selector_all('[data-self-name]')
            
            for element in elements:
                try:
                    name = await element.get_attribute("data-self-name")
                    if not name or not name.strip():
                        continue
                    
                    # Validate it's a real participant
                    if is_ui_element(name):
                        logger.debug(f"DOM: Skipping UI element '{name}'")
                        continue
                    
                    # Check if it's in a list item context
                    is_in_listitem = await element.evaluate("""
                        el => {
                            const listItem = el.closest('[role="listitem"]');
                            return listItem !== null;
                        }
                    """)
                    
                    if not is_in_listitem:
                        logger.debug(f"DOM: Skipping '{name}' - not in listitem")
                        continue
                    
                    # Clean the name
                    original_name = name.strip()
                    clean_name = original_name
                    is_bot = False
                    
                    # Check for (You) suffix
                    you_pattern = re.compile(r'\s*\(you\)$', re.IGNORECASE)
                    if you_pattern.search(clean_name):
                        clean_name = you_pattern.sub('', clean_name).strip()
                        is_bot = True
                    
                    # ENHANCED: Additional bot detection via DOM
                    if not is_bot:
                        is_bot = await element.evaluate("""
                            el => {
                                const listItem = el.closest('[role="listitem"]');
                                if (!listItem) return false;
                                
                                // Check for self-mute controls
                                const muteBtn = listItem.querySelector('[aria-label*="Mute microphone" i], [aria-label*="Turn off microphone" i]');
                                if (muteBtn) return true;
                                
                                // Check inner text for (You)
                                const innerText = (listItem.innerText || '').toLowerCase();
                                if (innerText.includes('(you)')) return true;
                                
                                // Check for self classes
                                const classList = Array.from(listItem.classList || []).join(' ').toLowerCase();
                                if (classList.includes('self') || classList.includes('local')) return true;
                                
                                return false;
                            }
                        """)
                    
                    if clean_name and len(clean_name) > 1:
                        participants.append({
                            "name": clean_name,
                            "role": "guest",
                            "is_speaking": False,
                            "is_bot": is_bot,
                            "original_name": original_name,
                        })
                        logger.debug(f"DOM: Added '{clean_name}' (is_bot: {is_bot})")
                        
                except Exception as e:
                    logger.debug(f"DOM: Error processing element: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"DOM selector extraction failed: {e}")
        
        return participants
    
    async def _extract_via_panel_text(self, page: Page) -> List[Dict]:
        """Extract by reading People panel text - with strict filtering and enhanced bot detection."""
        participants = []
        seen_names = set()
        
        try:
            # Find participant list items
            list_items = await page.query_selector_all('[role="listitem"]')
            
            for item in list_items:
                try:
                    # Get text content
                    text = await item.inner_text()
                    if not text or len(text.strip()) < 2:
                        continue
                    
                    # Full text check - skip obvious UI elements
                    if is_ui_element(text):
                        logger.debug(f"Panel: Skipping UI element: {text[:50]}...")
                        continue
                    
                    # Try to find the actual name
                    name = None
                    
                    # Method 1: data-self-name attribute
                    name_el = await item.query_selector('[data-self-name]')
                    if name_el:
                        name = await name_el.get_attribute("data-self-name")
                    
                    # Method 2: span with dir="auto"
                    if not name:
                        name_el = await item.query_selector('span[dir="auto"], div[dir="auto"]')
                        if name_el:
                            name = await name_el.inner_text()
                    
                    # Method 3: First line of text (very careful)
                    if not name:
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        for line in lines:
                            if not is_ui_element(line) and len(line) > 1 and len(line) < 100:
                                name = line
                                break
                    
                    if name and name.strip():
                        # Final validation
                        if is_ui_element(name):
                            logger.debug(f"Panel: Filtered out '{name}' (UI element)")
                            continue
                        
                        original_name = name.strip()
                        clean_name = original_name
                        is_bot = False
                        
                        # Check for (You) suffix
                        you_pattern = re.compile(r'\s*\(you\)$', re.IGNORECASE)
                        if you_pattern.search(clean_name):
                            clean_name = you_pattern.sub('', clean_name).strip()
                            is_bot = True
                        
                        # ENHANCED: Check for other self indicators in text
                        if not is_bot:
                            text_lower = text.lower()
                            if '(you)' in text_lower:
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
                                logger.debug(f"Panel: Added '{clean_name}' (is_bot: {is_bot})")
                                
                except Exception as e:
                    logger.debug(f"Panel: Error processing list item: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Panel text extraction failed: {e}")
        
        return participants
    
    async def _ensure_people_panel_open(self, page: Page) -> None:
        """Ensure People panel is open - with multiple attempts."""
        try:
            # Check if panel is already open
            panel_selectors = [
                '[aria-label*="People" i][role="dialog"]',
                '[aria-label*="Show everyone" i]',
                '[role="dialog"]:has([role="list"])',
            ]
            
            for selector in panel_selectors:
                try:
                    panel = await page.query_selector(f'{selector}:visible')
                    if panel:
                        logger.debug("People panel already open")
                        return
                except Exception:
                    continue
            
            # Try to open People panel
            button_selectors = [
                '[aria-label*="Show everyone" i]',
                '[aria-label*="People" i]',
                'button[aria-label*="People" i]',
                'button[data-tooltip*="People" i]',
                '[data-tooltip*="Show everyone" i]',
            ]
            
            for selector in button_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        await button.click()
                        await page.wait_for_timeout(1500)
                        logger.info(f"Opened People panel via: {selector}")
                        return
                except Exception:
                    continue
            
            logger.warning("Could not find/open People panel - extraction may be limited")
                    
        except Exception as e:
            logger.debug(f"Error opening People panel: {e}")
