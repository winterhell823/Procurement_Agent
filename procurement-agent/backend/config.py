import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Get the root directory where the .env file is located
ROOT_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Database Settings
    POSTGRES_USER:     str = "procurement_user"
    POSTGRES_PASSWORD: str = "procurement_pass"
    POSTGRES_DB:       str = "procurement"
    POSTGRES_HOST:     str = "localhost"
    POSTGRES_PORT:     int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    DEBUG: bool = True

    # Auth
    SECRET_KEY:        str = ""
    JWT_ALGORITHM:     str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    GOOGLE_CLIENT_ID:  str = ""

    # External APIs
    TINYFISH_API_KEY:  str = ""
    TINYFISH_BASE_URL: str = "https://api.tinyfish.ai"
    OPENAI_API_KEY:    str = ""
    OPENAI_MODEL:      str = "gpt-4o"
    SENDGRID_API_KEY:  Optional[str] = None
    FROM_EMAIL:        str = "noreply@procurement-agent.com"

    # Social/Communications
    TELEGRAM_BOT_TOKEN:   Optional[str] = None
    TWILIO_ACCOUNT_SID:    Optional[str] = None
    TWILIO_AUTH_TOKEN:     Optional[str] = None
    TWILIO_WHATSAPP_FROM:  Optional[str] = "whatsapp:+14155238886"
    EXCHANGE_RATE_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        extra="ignore",
        env_prefix=""  # No prefix for env vars
    )

    # Manual mapping for non-matching names
    def __init__(self, **values):
        super().__init__(**values)
        # If JWT_SECRET is in env but we named it SECRET_KEY
        val = os.getenv("JWT_SECRET")
        if val:
            self.SECRET_KEY = val

settings = Settings()
 
