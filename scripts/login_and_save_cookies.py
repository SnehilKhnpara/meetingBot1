#!/usr/bin/env python3
"""
One-time script to log in to Google Meet and save authentication cookies.

Usage:
    python scripts/login_and_save_cookies.py --platform gmeet
    python scripts/login_and_save_cookies.py --platform teams
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
from src.cookie_manager import get_cookie_manager
from src.logging_utils import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)


async def login_and_save_cookies(platform: str) -> None:
    """Perform manual login and save cookies."""
    cookie_manager = get_cookie_manager()
    
    print(f"\n{'='*60}")
    print(f"Google Meet Login Script - {platform.upper()}")
    print(f"{'='*60}\n")
    print("This script will:")
    print("1. Open a browser window")
    print("2. Navigate to Google Meet")
    print("3. YOU will manually sign in (pass CAPTCHA/2FA)")
    print("4. After successful login, cookies will be saved")
    print("\nPress Ctrl+C to cancel\n")
    
    try:
        input("Press Enter to start...")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Must be visible for manual login
            args=[
                "--disable-blink-features=AutomationControlled",
                "--exclude-switches=enable-automation",
                "--disable-infobars",
            ],
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        
        page = await context.new_page()
        
        # Remove automation detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print("\n🌐 Opening Google Meet...")
        
        if platform.lower() == "gmeet":
            url = "https://meet.google.com"
        elif platform.lower() == "teams":
            url = "https://teams.microsoft.com"
        else:
            print(f"❌ Unknown platform: {platform}")
            return
        
        await page.goto(url, wait_until="domcontentloaded")
        print(f"✅ Navigated to {url}")
        print("\n" + "="*60)
        print("👤 NOW: Sign in manually in the browser window")
        print("   - Complete CAPTCHA if shown")
        print("   - Enter 2FA code if required")
        print("   - Wait until you're fully signed in")
        print("\n   Once signed in, come back here...")
        print("="*60 + "\n")
        
        # Wait for user to sign in
        signed_in = False
        check_count = 0
        
        while not signed_in and check_count < 60:  # 5 minutes max
            await asyncio.sleep(5)
            check_count += 1
            
            current_url = page.url.lower()
            page_content = (await page.content()).lower()
            
            # Check if signed in
            if platform.lower() == "gmeet":
                # Check for Google account indicators
                signed_in = (
                    "accounts.google.com" not in current_url and
                    ("sign in" not in page_content and "signin" not in page_content) and
                    (page.url.startswith("https://meet.google.com") or
                     "myaccount.google.com" in current_url or
                     "google.com/accounts" not in current_url)
                )
                # Additional check: try to find Google profile icon/account button
                try:
                    account_button = await page.query_selector('[aria-label*="Google Account"], [data-testid*="account"], img[alt*="Account"]')
                    if account_button:
                        signed_in = True
                except Exception:
                    pass
            elif platform.lower() == "teams":
                signed_in = (
                    "teams.microsoft.com" in current_url and
                    "sign in" not in page_content and
                    "login" not in page_content
                )
            
            if check_count % 6 == 0:  # Every 30 seconds
                print(f"⏳ Still waiting... ({check_count * 5}s elapsed)")
                print("   Make sure you're fully signed in in the browser window.")
        
        if not signed_in:
            print("\n❌ Timeout: Could not detect successful sign-in.")
            print("   Please try again or check if sign-in completed.")
            await browser.close()
            return
        
        print("\n✅ Sign-in detected! Saving cookies...")
        
        # Get storage state (includes cookies)
        storage_state = await context.storage_state()
        
        # Save cookies
        cookie_file = await cookie_manager.save_cookies(platform.lower(), storage_state)
        
        print(f"\n✅ Cookies saved successfully!")
        print(f"   Location: {cookie_file}")
        print(f"\n🎉 Done! Bot can now join {platform} meetings without sign-in.")
        print("\nYou can close the browser window now.\n")
        
        # Keep browser open for a bit so user can see
        await asyncio.sleep(3)
        await browser.close()


async def main():
    parser = argparse.ArgumentParser(description="Login and save cookies for meeting bot")
    parser.add_argument(
        "--platform",
        choices=["gmeet", "teams"],
        required=True,
        help="Platform to log in to",
    )
    args = parser.parse_args()
    
    try:
        await login_and_save_cookies(args.platform)
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Login script failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

