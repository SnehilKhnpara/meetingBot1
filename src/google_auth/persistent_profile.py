"""
Persistent Google Profile Manager

Manages isolated browser profiles for Google Meet authentication.
Each profile maintains its own login state and can be used independently.
"""
import asyncio
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import BrowserContext, Page

from ..config import get_settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileStatus:
    """Status of a Google profile."""
    profile_name: str
    profile_path: Path
    is_logged_in: bool
    is_available: bool
    last_used: Optional[datetime] = None
    session_id: Optional[str] = None  # Which session is using this profile


class PersistentProfileManager:
    """Manages multiple isolated Google Meet profiles for concurrent sessions."""
    
    def __init__(self, profiles_root: str = "profiles"):
        self.profiles_root = Path(profiles_root)
        self.profiles_root.mkdir(parents=True, exist_ok=True)
        self._profile_locks: Dict[str, asyncio.Lock] = {}
        self._active_sessions: Dict[str, str] = {}  # session_id -> profile_name
        
    def _get_profile_path(self, profile_name: str) -> Path:
        """Get full path to a profile directory."""
        return self.profiles_root / profile_name
    
    def _get_lock(self, profile_name: str) -> asyncio.Lock:
        """Get or create a lock for a profile."""
        if profile_name not in self._profile_locks:
            self._profile_locks[profile_name] = asyncio.Lock()
        return self._profile_locks[profile_name]
    
    def list_profiles(self) -> list[str]:
        """List all available profile directories."""
        if not self.profiles_root.exists():
            return []
        
        profiles = []
        for item in self.profiles_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it looks like a valid browser profile
                if (item / "Default").exists() or (item / "Preferences").exists() or (item / "Local State").exists():
                    profiles.append(item.name)
        return sorted(profiles)
    
    def create_profile(self, profile_name: str) -> Path:
        """Create a new empty profile directory."""
        profile_path = self._get_profile_path(profile_name)
        profile_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Created new profile: {profile_name}",
            extra={
                "extra_data": {
                    "profile_name": profile_name,
                    "profile_path": str(profile_path),
                }
            },
        )
        return profile_path
    
    def get_profile_status(self, profile_name: str) -> ProfileStatus:
        """Get status of a profile."""
        profile_path = self._get_profile_path(profile_name)
        is_available = profile_name not in self._active_sessions.values()
        
        # Check if profile directory exists
        if not profile_path.exists():
            return ProfileStatus(
                profile_name=profile_name,
                profile_path=profile_path,
                is_logged_in=False,
                is_available=True,
            )
        
        # Try to determine if logged in by checking for Google cookies
        is_logged_in = self._check_profile_logged_in(profile_path)
        
        # Find which session is using this profile
        session_id = None
        for sid, pname in self._active_sessions.items():
            if pname == profile_name:
                session_id = sid
                break
        
        return ProfileStatus(
            profile_name=profile_name,
            profile_path=profile_path,
            is_logged_in=is_logged_in,
            is_available=is_available,
            session_id=session_id,
        )
    
    def _check_profile_logged_in(self, profile_path: Path) -> bool:
        """Check if profile has Google login cookies."""
        # Check for Google cookies in the profile
        cookies_paths = [
            profile_path / "Default" / "Cookies",
            profile_path / "Cookies",  # Some profile structures
        ]
        
        for cookies_path in cookies_paths:
            if cookies_path.exists():
                # Cookie file exists - assume logged in (Playwright will validate on use)
                return True
        
        # Check for Local State which indicates profile has been used
        local_state = profile_path / "Local State"
        if local_state.exists():
            try:
                with open(local_state, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # Check if profile has account info
                    profile_info = state.get("profile", {})
                    if profile_info.get("info_cache") or profile_info.get("name"):
                        return True
            except Exception:
                pass
        
        return False
    
    async def allocate_profile(self, session_id: str, prefer_profile: Optional[str] = None) -> str:
        """
        Allocate an available profile for a session.
        
        Args:
            session_id: Unique session identifier
            prefer_profile: Preferred profile name (e.g., 'google_main')
        
        Returns:
            Profile name allocated to this session
        """
        settings = get_settings()
        
        # If a preferred profile is specified and available, use it
        if prefer_profile:
            status = self.get_profile_status(prefer_profile)
            if status.is_available:
                self._active_sessions[session_id] = prefer_profile
                logger.info(
                    f"Allocated preferred profile: {prefer_profile}",
                    extra={
                        "extra_data": {
                            "session_id": session_id,
                            "profile_name": prefer_profile,
                        }
                    },
                )
                return prefer_profile
        
        # Try main profile first
        main_profile = settings.gmeet_profile_name
        main_status = self.get_profile_status(main_profile)
        if main_status.is_available:
            self._active_sessions[session_id] = main_profile
            logger.info(
                f"Allocated main profile: {main_profile}",
                extra={
                    "extra_data": {
                        "session_id": session_id,
                        "profile_name": main_profile,
                    }
                },
            )
            return main_profile
        
        # Find first available profile
        all_profiles = self.list_profiles()
        for profile_name in all_profiles:
            status = self.get_profile_status(profile_name)
            if status.is_available:
                self._active_sessions[session_id] = profile_name
                logger.info(
                    f"Allocated available profile: {profile_name}",
                    extra={
                        "extra_data": {
                            "session_id": session_id,
                            "profile_name": profile_name,
                        }
                    },
                )
                return profile_name
        
        # Create a new profile if none available
        # Use pattern: google_1, google_2, etc.
        counter = 1
        while True:
            new_profile_name = f"google_{counter}"
            if new_profile_name not in all_profiles:
                self.create_profile(new_profile_name)
                self._active_sessions[session_id] = new_profile_name
                logger.info(
                    f"Created and allocated new profile: {new_profile_name}",
                    extra={
                        "extra_data": {
                            "session_id": session_id,
                            "profile_name": new_profile_name,
                        }
                    },
                )
                return new_profile_name
            counter += 1
    
    def release_profile(self, session_id: str) -> None:
        """Release a profile after session ends."""
        if session_id in self._active_sessions:
            profile_name = self._active_sessions.pop(session_id)
            logger.info(
                f"Released profile: {profile_name}",
                extra={
                    "extra_data": {
                        "session_id": session_id,
                        "profile_name": profile_name,
                    }
                },
            )
    
    async def validate_profile_login(self, profile_name: str, context: BrowserContext) -> tuple[bool, Optional[str]]:
        """
        Validate that a profile is logged into Google.
        
        Args:
            profile_name: Name of the profile to validate
            context: Browser context using this profile
        
        Returns:
            (is_logged_in, error_message)
        """
        try:
            # Create a test page
            page = await context.new_page()
            
            try:
                # Navigate to Google account page
                await page.goto("https://accounts.google.com/", wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(2000)
                
                # Check if we're on sign-in page or account page
                current_url = page.url
                page_content = (await page.content()).lower()
                
                # If URL contains 'ServiceLogin' or 'signin', we're not logged in
                if "servicelogin" in current_url.lower() or "signin" in current_url.lower():
                    return False, "Profile not logged in - redirecting to sign-in page"
                
                # Check for logged-in indicators
                logged_in_indicators = [
                    "myaccount.google.com" in current_url,
                    "accountchooser" in current_url,
                    "welcome" in page_content,
                ]
                
                if any(logged_in_indicators):
                    return True, None
                
                # Check for sign-in buttons
                sign_in_selectors = [
                    'text="Sign in"',
                    'a[href*="ServiceLogin"]',
                    '[aria-label*="Sign in"]',
                ]
                
                for selector in sign_in_selectors:
                    try:
                        el = await page.query_selector(selector)
                        if el and await el.is_visible():
                            return False, "Profile shows sign-in prompt - not authenticated"
                    except Exception:
                        continue
                
                # If we got here, assume logged in (might be on a different Google page)
                return True, None
                
            finally:
                await page.close()
                
        except Exception as e:
            error_msg = f"Failed to validate profile login: {str(e)}"
            logger.warning(
                error_msg,
                extra={
                    "extra_data": {
                        "profile_name": profile_name,
                        "error": str(e),
                    }
                },
            )
            return False, error_msg


# Global instance
_profile_manager: Optional[PersistentProfileManager] = None


def get_profile_manager() -> PersistentProfileManager:
    """Get the global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        settings = get_settings()
        _profile_manager = PersistentProfileManager(profiles_root=settings.profiles_root)
    return _profile_manager



