"""Secure credential storage and management for automatic login."""
import json
import base64
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import get_settings
from .logging_utils import get_logger


logger = get_logger(__name__)


class CredentialManager:
    """Manages encrypted credentials for automatic login."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.credentials_dir = self.data_dir / "credentials"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self._encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for credentials."""
        key_env = self.settings.cookie_encryption_key  # Reuse same key for simplicity
        if key_env:
            try:
                if isinstance(key_env, str):
                    return key_env.encode()
                return key_env
            except Exception:
                logger.warning("Invalid encryption key format, generating new one")
        
        # Generate deterministic key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"meeting_bot_cred_salt",
            iterations=100000,
        )
        key_material = kdf.derive(str(self.data_dir).encode())
        return base64.urlsafe_b64encode(key_material)
    
    def save_credentials(self, platform: str, email: str, password: str) -> str:
        """Save encrypted credentials. Returns file path."""
        credentials = {
            "platform": platform,
            "email": email,
            "password": password,
        }
        
        # Encrypt credentials
        encrypted_data = self._encrypt(json.dumps(credentials).encode())
        
        credential_file = self.credentials_dir / f"{platform}_credentials.enc"
        with open(credential_file, "wb") as f:
            f.write(encrypted_data)
        
        logger.info(
            f"Saved credentials for {platform}",
            extra={"extra_data": {"platform": platform, "email": email}},
        )
        return str(credential_file)
    
    def load_credentials(self, platform: str) -> Optional[dict]:
        """Load credentials for platform. Returns {email, password} or None."""
        settings = get_settings()
        
        # First, try environment variables (for quick setup)
        if platform == "gmeet" and settings.gmeet_email and settings.gmeet_password:
            logger.info(
                f"Using credentials from environment variables for {platform}",
                extra={"extra_data": {"platform": platform, "email": settings.gmeet_email}},
            )
            return {
                "email": settings.gmeet_email,
                "password": settings.gmeet_password,
            }
        
        # Then, try encrypted file storage
        credential_file = self.credentials_dir / f"{platform}_credentials.enc"
        
        if not credential_file.exists():
            logger.debug(
                f"No credentials found for {platform}",
                extra={"extra_data": {"platform": platform}},
            )
            return None
        
        try:
            with open(credential_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self._decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            logger.info(
                f"Loaded credentials for {platform}",
                extra={"extra_data": {"platform": platform, "email": credentials.get("email")}},
            )
            return {
                "email": credentials.get("email"),
                "password": credentials.get("password"),
            }
        except Exception as e:
            logger.error(
                f"Failed to load credentials for {platform}: {e}",
                extra={"extra_data": {"platform": platform, "error": str(e)}},
            )
            return None
    
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt credential data."""
        f = Fernet(self._encryption_key)
        return f.encrypt(data)
    
    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt credential data."""
        f = Fernet(self._encryption_key)
        return f.decrypt(encrypted_data)
    
    def credentials_exist(self, platform: str) -> bool:
        """Check if credentials exist for platform."""
        credential_file = self.credentials_dir / f"{platform}_credentials.enc"
        return credential_file.exists()


# Global instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get or create global CredentialManager instance."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager

