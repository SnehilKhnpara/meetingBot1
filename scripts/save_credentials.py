#!/usr/bin/env python3
"""
Save login credentials securely for automatic login.

Usage:
    python scripts/save_credentials.py --platform gmeet --email your@email.com
"""
import asyncio
import argparse
import sys
import getpass
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.credential_manager import get_credential_manager
from src.logging_utils import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)


async def save_credentials(platform: str, email: str, password: str) -> None:
    """Save credentials securely."""
    credential_manager = get_credential_manager()
    
    print(f"\n{'='*60}")
    print(f"Saving Credentials - {platform.upper()}")
    print(f"{'='*60}\n")
    
    try:
        credential_file = credential_manager.save_credentials(platform, email, password)
        print(f"✅ Credentials saved successfully!")
        print(f"   Email: {email}")
        print(f"   Platform: {platform}")
        print(f"   Location: {credential_file}")
        print(f"\n🎉 Bot will now automatically login with these credentials.\n")
    except Exception as e:
        print(f"\n❌ Error saving credentials: {e}\n")
        logger.exception("Failed to save credentials")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Save login credentials for automatic login")
    parser.add_argument(
        "--platform",
        choices=["gmeet", "teams"],
        required=True,
        help="Platform to save credentials for",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address for login",
    )
    parser.add_argument(
        "--password",
        help="Password (optional, will prompt if not provided or use GMEET_PASSWORD env var)",
    )
    args = parser.parse_args()
    
    # Get password from env var, command line, or prompt
    import os
    password = args.password or os.getenv("GMEET_PASSWORD")
    
    if not password:
        password = getpass.getpass(f"Enter password for {args.email}: ")
    
    if not password:
        print("❌ Password cannot be empty!")
        sys.exit(1)
    
    try:
        asyncio.run(save_credentials(args.platform, args.email, password))
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Credential save script failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

