#!/usr/bin/env python3
"""Generate a Fernet encryption key for cookie storage."""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("=" * 60)
    print("Cookie Encryption Key (save this securely!)")
    print("=" * 60)
    print(key.decode())
    print("=" * 60)
    print("\nTo use this key, set environment variable:")
    print(f"  COOKIE_ENCRYPTION_KEY={key.decode()}")
    print("\nOr add to your .env file:")
    print(f"COOKIE_ENCRYPTION_KEY={key.decode()}")




