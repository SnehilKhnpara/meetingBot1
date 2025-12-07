"""
Filter out UI elements and notifications from participant names.

Google Meet shows various UI notifications that should not be treated as participants.
"""
from typing import Optional


# HARD BLACKLIST: UI text that must NEVER be treated as participant names
# These are exact matches or substrings that indicate UI elements, not real users
UI_NOTIFICATION_BLACKLIST = [
    # From actual session data - EXACT matches that were incorrectly captured
    "backgrounds and effects",
    "you can't unmute someone else",
    "your microphone is off.",
    "your microphone is off",
    "you can't remotely mute",
    
    # Settings and effects panel
    "visual effects",
    "apply visual effects",
    "background blur",
    "blur background",
    "change background",
    
    # Microphone/camera notifications  
    "your camera is off",
    "microphone is off",
    "camera is off",
    "microphone is on",
    "camera is on",
    "mic is off",
    "mic is on",
    
    # Remote mute/unmute notifications (with participant names embedded)
    "can't remotely mute",
    "can't unmute",
    "remotely mute",
    "'s microphone",  # "John's microphone" - should extract "John" separately
    
    # Meeting controls and buttons
    "turn on microphone",
    "turn off microphone", 
    "turn on camera",
    "turn off camera",
    "mute microphone",
    "unmute microphone",
    "present now",
    "stop presenting",
    "share screen",
    "stop sharing",
    "raise hand",
    "lower hand",
    "end call",
    "leave call",
    "leave meeting",
    "end meeting",
    
    # Panel headers and sections
    "in the meeting",
    "contributors",
    "add people",
    "search for people",
    "invite",
    "share link",
    "host controls",
    "meeting details",
    "other people",
    "in this call",
    "people in this call",
    
    # Waiting/connection states
    "you're the only one",
    "waiting for others",
    "connecting",
    "reconnecting",
    "joining",
    "loading",
    
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
    "denied",
    "blocked",
    
    # Button text
    "turn on",
    "turn off",
    "mute",
    "unmute",
    "join now",
    "ask to join",
    "present",
]

# Patterns that indicate UI notifications, not participant names
UI_NOTIFICATION_PATTERNS = UI_NOTIFICATION_BLACKLIST


def is_valid_participant_name(name: str) -> bool:
    """
    CRITICAL: Check if a name is a valid participant name (not a UI notification).
    
    This function uses a HARD BLACKLIST to ensure UI text is NEVER treated as a participant.
    
    Args:
        name: The name to validate
        
    Returns:
        True if valid participant name, False if UI element
    """
    if not name or not isinstance(name, str):
        return False
    
    name_lower = name.strip().lower()
    
    # Empty
    if not name_lower:
        return False
    
    # CRITICAL: Hard blacklist check - exact matches first
    for blacklisted in UI_NOTIFICATION_BLACKLIST:
        blacklisted_lower = blacklisted.lower()
        if blacklisted_lower == name_lower:
            return False
        if blacklisted_lower in name_lower:
            return False
    
    # Check against known UI patterns
    for pattern in UI_NOTIFICATION_PATTERNS:
        if pattern.lower() in name_lower:
            return False
    
    # Check if it starts with "your" or "you" (UI notifications)
    if name_lower.startswith("your ") or name_lower.startswith("you "):
        return False
    
    # Check if it contains "can't" or "cannot" (UI messages)
    if "can't" in name_lower or "cannot" in name_lower:
        return False
    
    # Check for possessive patterns with microphone/camera (e.g., "John's microphone")
    if "'s microphone" in name_lower or "'s camera" in name_lower:
        return False
    
    # Check if it's a sentence (notifications are usually sentences)
    # But allow names with titles like "Dr. John Smith"
    if name.count(".") > 1 and len(name.split()) > 4:
        # Likely a notification message with multiple sentences
        return False
    
    # Check if ends with period and is long (likely notification)
    if name_lower.endswith(".") and len(name.split()) > 4:
        return False
    
    # Too short
    if len(name_lower) < 2:
        return False
    
    # Too long (likely not a name)
    if len(name) > 100:
        return False
    
    # Must contain at least one letter
    if not any(c.isalpha() for c in name):
        return False
    
    # All uppercase and contains digits (likely system text like "ERROR123")
    if name.isupper() and any(c.isdigit() for c in name):
        return False
    
    return True


def clean_participant_name(name: str) -> Optional[str]:
    """
    Clean and validate a participant name.
    
    Args:
        name: Raw name from UI
        
    Returns:
        Cleaned name if valid, None if UI element
    """
    if not name or not isinstance(name, str):
        return None
    
    # Strip whitespace
    cleaned = name.strip()
    
    # Remove "(You)" suffix but keep the name
    if cleaned.endswith(" (You)"):
        cleaned = cleaned[:-6].strip()
    
    # Validate
    if is_valid_participant_name(cleaned):
        return cleaned
    
    return None
