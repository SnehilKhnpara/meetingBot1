import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .config import get_settings
from .cookie_manager import get_cookie_manager
from .logging_utils import get_logger


logger = get_logger(__name__)


class PlaywrightManager:
    """Singleton-style Playwright launcher reused across sessions."""

    _instance_lock = asyncio.Lock()
    _instance: Optional["PlaywrightManager"] = None

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Optional[Browser | BrowserContext] = None
        self._ready = asyncio.Event()

    @classmethod
    async def get(cls) -> "PlaywrightManager":
        async with cls._instance_lock:
            if cls._instance is None:
                cls._instance = PlaywrightManager()
                await cls._instance._start()
        return cls._instance

    async def _start(self) -> None:
        settings = get_settings()
        logger.info(
            "Starting Playwright",
            extra={
                "extra_data": {
                    "component": "playwright",
                    "headless": settings.headless,
                    "profiles_root": settings.profiles_root,
                    "gmeet_profile_name": settings.gmeet_profile_name,
                }
            },
        )
        self._playwright = await async_playwright().start()
        
        # Chrome args for stability and nicer window
        chrome_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--start-maximized",  # Start maximized for better view
        ]

        # Persistent Google Meet profile using launch_persistent_context
        # This keeps you signed in across all sessions.
        profiles_root = Path(settings.profiles_root)
        profile_dir = profiles_root / settings.gmeet_profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Launching persistent Chromium context for Google Meet",
            extra={
                "extra_data": {
                    "profile_dir": str(profile_dir),
                    "headed": not settings.headless,
                }
            },
        )

        # Use Playwright's bundled Chromium with a persistent user_data_dir.
        # This is the most stable configuration across environments.
        self._browser = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=settings.headless,
            args=chrome_args,
            viewport=None,
        )
        self._ready.set()

    async def ensure_running(self) -> None:
        # Browser in Playwright has `is_connected()`; reused after crashes by restarting.
        browser_needs_restart = (
            not self._ready.is_set()
            or self._browser is None
            or (isinstance(self._browser, Browser) and not self._browser.is_connected())
            or (isinstance(self._browser, BrowserContext) and self._browser.pages == [])
        )
        if browser_needs_restart:
            logger.warning(
                "Playwright browser not ready, restarting",
                extra={"extra_data": {"component": "playwright", "event": "restart"}},
            )
            await self._start()

    @asynccontextmanager
    async def new_context(self, platform: str = "gmeet") -> AsyncIterator[BrowserContext]:
        """Create browser context, optionally loading stored cookies."""
        await self.ensure_running()
        assert self._browser is not None
        settings = get_settings()
        
        # If using persistent context, browser IS the context
        if isinstance(self._browser, BrowserContext):
            yield self._browser
        else:
            # Normal browser, create new context
            # Try to load stored cookies if enabled
            storage_state = None
            if settings.use_stored_cookies:
                cookie_manager = get_cookie_manager()
                storage_state = await cookie_manager.load_cookies(platform)
                if storage_state:
                    logger.info(
                        f"Loading stored cookies for {platform}",
                        extra={"extra_data": {"platform": platform}},
                    )
                else:
                    logger.info(
                        f"No stored cookies found for {platform}, creating fresh context",
                        extra={"extra_data": {"platform": platform}},
                    )
            
            context = await self._browser.new_context(
                storage_state=storage_state,
            )
            try:
                yield context
            finally:
                await context.close()

    @asynccontextmanager
    async def new_page(self, platform: str = "gmeet") -> AsyncIterator[Page]:
        async with self.new_context(platform=platform) as context:
            page = await context.new_page()
            
            # Hide automation detection - make it look like normal browser
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Remove automation indicators
                delete navigator.__proto__.webdriver;
            """)
            
            try:
                yield page
            finally:
                await page.close()
