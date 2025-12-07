"""Cookie storage and management for Google Meet authentication."""
import json
import base64
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import get_settings
from .storage import blob_storage
from .logging_utils import get_logger


logger = get_logger(__name__)


class CookieManager:
    """Manages Google Meet authentication cookies with encryption and Azure storage."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.cookies_dir = self.data_dir / "cookies"
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        
        # Encryption key (derive from env or generate)
        self._encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for cookies. Returns Fernet-compatible key."""
        key_env = self.settings.cookie_encryption_key
        if key_env:
            try:
                # Key should be base64 URL-safe encoded string (Fernet format)
                if isinstance(key_env, str):
                    # If it's already a base64 string, decode it
                    return key_env.encode()
                return key_env
            except Exception:
                logger.warning("Invalid encryption key format, generating new one")
        
        # Generate deterministic key from data_dir (for dev, use env var in prod)
        # Fernet needs a URL-safe base64-encoded 32-byte key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"meeting_bot_cookie_salt",
            iterations=100000,
        )
        key_material = kdf.derive(str(self.data_dir).encode())
        # Fernet.generate_key() returns bytes that are already base64 URL-safe encoded
        return base64.urlsafe_b64encode(key_material)
    
    async def save_cookies(self, platform: str, storage_state: Dict[str, Any]) -> str:
        """Save cookies from Playwright storage state. Returns file path."""
        # Encrypt cookies before saving
        encrypted_data = self._encrypt(json.dumps(storage_state).encode())
        
        cookie_file = self.cookies_dir / f"{platform}_cookies.json.enc"
        with open(cookie_file, "wb") as f:
            f.write(encrypted_data)
        
        # Also save metadata
        metadata = {
            "platform": platform,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": self._estimate_expiry(storage_state),
        }
        metadata_file = self.cookies_dir / f"{platform}_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Upload to Azure if configured
        if blob_storage.service_client:
            try:
                await blob_storage.upload_bytes_with_retry(
                    f"cookies/{platform}_cookies.json.enc",
                    encrypted_data,
                    content_type="application/octet-stream",
                )
            except Exception as e:
                logger.warning(f"Failed to upload cookies to Azure: {e}")
        
        logger.info(
            f"Saved cookies for {platform}",
            extra={"extra_data": {"platform": platform, "cookie_file": str(cookie_file)}},
        )
        return str(cookie_file)
    
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt cookie data."""
        f = Fernet(self._encryption_key)
        return f.encrypt(data)
    
    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt cookie data."""
        f = Fernet(self._encryption_key)
        return f.decrypt(encrypted_data)
    
    def _estimate_expiry(self, storage_state: Dict[str, Any]) -> str:
        """Estimate when cookies will expire."""
        cookies = storage_state.get("cookies", [])
        if not cookies:
            # Default to 7 days
            return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        
        max_expiry = datetime.now(timezone.utc)
        for cookie in cookies:
            if "expires" in cookie:
                try:
                    expiry = datetime.fromtimestamp(cookie["expires"], tz=timezone.utc)
                    if expiry > max_expiry:
                        max_expiry = expiry
                except Exception:
                    pass
        
        return max_expiry.isoformat()
    
    async def load_cookies(self, platform: str) -> Optional[Dict[str, Any]]:
        """Load cookies for platform. Returns storage state dict or None."""
        cookie_file = self.cookies_dir / f"{platform}_cookies.json.enc"
        
        if not cookie_file.exists():
            logger.info(
                f"No cookies found for {platform}",
                extra={"extra_data": {"platform": platform}},
            )
            return None
        
        try:
            # Try local first
            with open(cookie_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self._decrypt(encrypted_data)
            storage_state = json.loads(decrypted_data.decode())
            
            # Check if expired
            if self._is_expired(platform):
                logger.warning(
                    f"Cookies for {platform} appear expired",
                    extra={"extra_data": {"platform": platform}},
                )
                return None
            
            logger.info(
                f"Loaded cookies for {platform}",
                extra={"extra_data": {"platform": platform}},
            )
            return storage_state
            
        except Exception as e:
            logger.error(
                f"Failed to load cookies for {platform}: {e}",
                extra={"extra_data": {"platform": platform, "error": str(e)}},
            )
            return None
    
    def _is_expired(self, platform: str) -> bool:
        """Check if cookies are expired."""
        metadata_file = self.cookies_dir / f"{platform}_metadata.json"
        if not metadata_file.exists():
            return False
        
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            expires_at = metadata.get("expires_at")
            if not expires_at:
                return False
            
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            is_expired = datetime.now(timezone.utc) > expiry
            return is_expired
        except Exception:
            return False
    
    def get_cookie_status(self, platform: str) -> Dict[str, Any]:
        """Get status of cookies (exists, expired, etc.)."""
        cookie_file = self.cookies_dir / f"{platform}_cookies.json.enc"
        metadata_file = self.cookies_dir / f"{platform}_metadata.json"
        
        status = {
            "platform": platform,
            "exists": cookie_file.exists(),
            "expired": False,
            "saved_at": None,
            "expires_at": None,
        }
        
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                status["saved_at"] = metadata.get("saved_at")
                status["expires_at"] = metadata.get("expires_at")
                status["expired"] = self._is_expired(platform)
            except Exception:
                pass
        
        return status


# Global instance
_cookie_manager: Optional[CookieManager] = None


def get_cookie_manager() -> CookieManager:
    """Get or create global CookieManager instance."""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager

