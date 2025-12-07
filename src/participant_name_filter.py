"""
Filter out UI elements and notifications from participant names.

Google Meet shows various UI notifications that should not be treated as participants.
"""
from typing import Optional


# HARD BLACKLIST: UI text that must NEVER be treated as participant names
# These are exact matches or substrings that indicate UI elements, not real users
UI_NOTIFICATION_BLACKLIST = [
    # Exact matches from your session data
    "backgrounds and effects",
    "you can't unmute someone else",
    "your microphone is off.",
    "you can't remotely mute",
    
    # Common UI patterns
    "your microphone is off",
    "your camera is off",
    "microphone is off",
    "camera is off",
    "you can't remotely mute",
    "you can't unmute",
    "can't remotely mute",
    "can't unmute",
    "remotely mute",
    "your microphone",
    "your camera",
    "microphone",
    "camera",
    "settings",
    "options",
    "more options",
    "you're the only one",
    "waiting for others",
    "connecting",
    "joining",
    "present now",
    "turn on",
    "turn off",
    "mute",
    "unmute",
    "enable",
    "disable",
    "allow",
    "deny",
    "permission",
    "access",
    "grant",
    "denied",
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
        if blacklisted.lower() == name_lower:
            return False
        if blacklisted.lower() in name_lower:
            return False
    
    # Check against known UI patterns
    for pattern in UI_NOTIFICATION_PATTERNS:
        if pattern in name_lower:
            return False
    
    # Check if it starts with "your" or "you" (UI notifications)
    if name_lower.startswith("your ") or name_lower.startswith("you "):
        return False
    
    # Check if it contains "can't" (UI messages)
    if "can't" in name_lower or "cannot" in name_lower:
        return False
    
    # Check if it's a sentence (notifications are usually sentences)
    if "." in name and len(name.split()) > 3:
        # Likely a notification message
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
