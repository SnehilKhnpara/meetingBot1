import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    environment: str = Field(default="dev")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Playwright / browser
    headless: bool = Field(default=False)  # Show browser by default
    max_concurrent_sessions: int = Field(default=10)
    session_start_timeout_seconds: int = Field(default=30)
    profiles_root: str = Field(
        default="profiles",
        description="Root directory for persistent browser profiles",
    )
    gmeet_profile_name: str = Field(
        default="google_main",
        description="Directory name under profiles_root for the main Google Meet profile",
    )
    
    # Local storage (instead of Azure)
    data_dir: str = Field(default="data", description="Directory for local data storage")

    # Azure (placeholders, wired later)
    azure_blob_connection_string: str | None = Field(default=None)
    azure_blob_container: str | None = Field(default=None)

    azure_eventgrid_endpoint: str | None = Field(default=None)
    azure_eventgrid_key: str | None = Field(default=None)

    # External diarisation service (optional)
    diarization_api_url: str | None = Field(
        default=None, description="Optional HTTP endpoint for diarisation"
    )
    
    # Google authentication
    google_login_required: bool = Field(
        default=True,
        description="Require valid Google login before joining meetings. If false, bot will attempt join without validation."
    )
    max_concurrent_meetings: int = Field(
        default=5,
        description="Maximum number of concurrent meeting sessions (each uses a separate profile)"
    )
    
    # Bot identity
    bot_display_name: str = Field(
        default="Meeting Bot",
        description="Display name used to identify the bot in participant lists. Bot will only leave when it's the only participant with this name."
    )
    
    # Cookie-based authentication (optional, legacy)
    cookie_encryption_key: str | None = Field(
        default=None, description="Base64 encryption key for cookies (generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
    )
    use_stored_cookies: bool = Field(
        default=False, description="Use stored cookies for authentication (deprecated - use persistent profiles instead)"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("ENVIRONMENT", "dev"),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        headless=os.getenv("HEADLESS", "false").lower() == "true",  # Default to visible browser
        max_concurrent_sessions=int(os.getenv("MAX_CONCURRENT_SESSIONS", "10")),
        session_start_timeout_seconds=int(
            os.getenv("SESSION_START_TIMEOUT_SECONDS", "30")
        ),
        azure_blob_connection_string=os.getenv("AZURE_BLOB_CONNECTION_STRING"),
        azure_blob_container=os.getenv("AZURE_BLOB_CONTAINER"),
        azure_eventgrid_endpoint=os.getenv("AZURE_EVENTGRID_ENDPOINT"),
        azure_eventgrid_key=os.getenv("AZURE_EVENTGRID_KEY"),
        diarization_api_url=os.getenv("DIARIZATION_API_URL"),
        data_dir=os.getenv("DATA_DIR", "data"),
        profiles_root=os.getenv("PROFILES_ROOT", "profiles"),
        gmeet_profile_name=os.getenv("GMEET_PROFILE_NAME", "google_main"),
        google_login_required=os.getenv("GOOGLE_LOGIN_REQUIRED", "true").lower() == "true",
        max_concurrent_meetings=int(os.getenv("MAX_CONCURRENT_MEETINGS", "5")),
        cookie_encryption_key=os.getenv("COOKIE_ENCRYPTION_KEY"),
        use_stored_cookies=os.getenv("USE_STORED_COOKIES", "false").lower() == "true",
        bot_display_name=os.getenv("BOT_DISPLAY_NAME", "Meeting Bot"),
    )



