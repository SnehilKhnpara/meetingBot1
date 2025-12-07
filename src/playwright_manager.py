"""
Enhanced Playwright Manager with per-session profile support.

Each session gets its own isolated browser context using a dedicated profile.
This allows multiple concurrent meetings without conflicts.
"""
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from playwright.async_api import async_playwright, BrowserContext, Page

from .config import get_settings
from .logging_utils import get_logger
from .google_auth.persistent_profile import get_profile_manager

logger = get_logger(__name__)


class EnhancedPlaywrightManager:
    """Playwright manager with per-session profile allocation."""
    
    _instance_lock = asyncio.Lock()
    _instance: Optional["EnhancedPlaywrightManager"] = None
    _playwright = None
    
    def __init__(self):
        self._playwright = None
        self._profile_contexts: dict[str, BrowserContext] = {}  # profile_name -> context
        self._context_locks: dict[str, asyncio.Lock] = {}
    
    @classmethod
    async def get(cls) -> "EnhancedPlaywrightManager":
        """Get or create the singleton instance."""
        async with cls._instance_lock:
            if cls._instance is None:
                cls._instance = EnhancedPlaywrightManager()
                await cls._instance._initialize()
            return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize Playwright."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            logger.info(
                "Enhanced Playwright manager initialized",
                extra={"extra_data": {"component": "playwright_manager"}},
            )
    
    def _get_context_lock(self, profile_name: str) -> asyncio.Lock:
        """Get or create a lock for a profile context."""
        if profile_name not in self._context_locks:
            self._context_locks[profile_name] = asyncio.Lock()
        return self._context_locks[profile_name]
    
    async def _get_or_create_context(self, profile_name: str) -> BrowserContext:
        """
        Get or create a browser context for a profile.
        Each profile gets its own isolated context.
        """
        async with self._get_context_lock(profile_name):
            if profile_name in self._profile_contexts:
                context = self._profile_contexts[profile_name]
                # Check if context is still valid
                if not context.pages or len(context.pages) == 0:
                    # Context is empty, might be closed - create new one
                    try:
                        await context.close()
                    except Exception:
                        pass
                    del self._profile_contexts[profile_name]
                else:
                    return context
            
            # Create new context for this profile
            settings = get_settings()
            profile_manager = get_profile_manager()
            profile_path = profile_manager._get_profile_path(profile_name)
            profile_path.mkdir(parents=True, exist_ok=True)
            
            chrome_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized",
            ]
            
            logger.info(
                f"Creating browser context for profile: {profile_name}",
                extra={
                    "extra_data": {
                        "component": "playwright_manager",
                        "profile_name": profile_name,
                        "profile_path": str(profile_path),
                        "headless": settings.headless,
                    }
                },
            )
            
            # Create persistent context for this profile
            context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                headless=settings.headless,
                args=chrome_args,
                viewport=None,
            )
            
            self._profile_contexts[profile_name] = context
            
            # Validate login if required
            if settings.google_login_required:
                profile_manager_instance = get_profile_manager()
                is_logged_in, error = await profile_manager_instance.validate_profile_login(
                    profile_name, context
                )
                if not is_logged_in:
                    logger.warning(
                        f"Profile {profile_name} login validation failed: {error}",
                        extra={
                            "extra_data": {
                                "profile_name": profile_name,
                                "error": error,
                            }
                        },
                    )
                    # Don't fail here - let the join flow handle it
            
            return context
    
    @asynccontextmanager
    async def new_page_for_session(
        self, session_id: str, platform: str = "gmeet"
    ) -> AsyncIterator[Page]:
        """
        Create a new page for a session using an allocated profile.
        
        The profile is automatically allocated and released.
        """
        profile_manager = get_profile_manager()
        
        # Allocate a profile for this session
        profile_name = await profile_manager.allocate_profile(session_id)
        
        try:
            # Get or create context for this profile
            context = await self._get_or_create_context(profile_name)
            
            # Create new page
            page = await context.new_page()
            
            # Hide automation detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
                delete navigator.__proto__.webdriver;
            """)
            
            logger.info(
                f"Created page for session using profile: {profile_name}",
                extra={
                    "extra_data": {
                        "session_id": session_id,
                        "profile_name": profile_name,
                        "platform": platform,
                    }
                },
            )
            
            try:
                yield page
            finally:
                await page.close()
                
        finally:
            # Release profile when done
            profile_manager.release_profile(session_id)
    
    async def shutdown(self) -> None:
        """Close all contexts and shutdown Playwright."""
        for profile_name, context in self._profile_contexts.items():
            try:
                await context.close()
            except Exception as e:
                logger.warning(f"Error closing context for {profile_name}: {e}")
        
        self._profile_contexts.clear()
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# Global instance
_manager_instance: Optional[EnhancedPlaywrightManager] = None


async def get_enhanced_manager() -> EnhancedPlaywrightManager:
    """Get the enhanced Playwright manager instance."""
    return await EnhancedPlaywrightManager.get()

