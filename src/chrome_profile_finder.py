"""Helper functions to find existing Chrome profiles."""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional


def get_chrome_profile_paths() -> List[Dict[str, str]]:
    """Find all Chrome user data directories and profiles on Windows."""
    profiles = []
    
    # Common Chrome user data locations on Windows
    chrome_paths = [
        Path(os.path.expanduser("~")) / "AppData" / "Local" / "Google" / "Chrome" / "User Data",
        Path(os.path.expanduser("~")) / "AppData" / "Local" / "Google" / "Chrome Beta" / "User Data",
        Path(os.path.expanduser("~")) / "AppData" / "Local" / "Google" / "Chrome Dev" / "User Data",
    ]
    
    for user_data_dir in chrome_paths:
        if not user_data_dir.exists():
            continue
        
        # Check for default profile
        default_profile = user_data_dir / "Default"
        if default_profile.exists():
            profiles.append({
                "name": "Default",
                "path": str(default_profile),
                "user_data_dir": str(user_data_dir),
                "type": "Default Profile",
            })
        
        # Check for multiple profiles in Local State
        local_state_file = user_data_dir / "Local State"
        if local_state_file.exists():
            try:
                with open(local_state_file, "r", encoding="utf-8") as f:
                    local_state = json.load(f)
                    profile_info = local_state.get("profile", {}).get("info_cache", {})
                    
                    for profile_id, profile_data in profile_info.items():
                        profile_name = profile_data.get("name", profile_id)
                        profile_path = user_data_dir / profile_id
                        
                        if profile_path.exists() and profile_id != "Default":
                            profiles.append({
                                "name": profile_name,
                                "path": str(profile_path),
                                "user_data_dir": str(user_data_dir),
                                "type": "Profile",
                                "profile_id": profile_id,
                            })
            except Exception:
                pass
    
    return profiles


def find_default_chrome_profile() -> Optional[str]:
    """Find the default Chrome profile path."""
    default_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default"
    if default_path.exists():
        return str(default_path.parent)  # Return User Data directory
    return None


def validate_chrome_profile_path(path: str) -> bool:
    """Validate if the given path is a valid Chrome profile or User Data directory."""
    profile_path = Path(path)
    
    if not profile_path.exists():
        return False
    
    # Check if it's a User Data directory (contains Default profile)
    if (profile_path / "Default").exists():
        return True
    
    # Check if it's a profile directory (contains Preferences file)
    if (profile_path / "Preferences").exists():
        return True
    
    return False




