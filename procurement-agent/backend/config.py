from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    #Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/procurement"
    DEBUG: bool = True

    #Auth
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    GOOGLE_CLIENT_ID: str = ""

    # TnyFish
    TINYFISH_API_KEY: str = ""
    TINYFISH_BASE_URL: str = "https://api.tinyfish.ai"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
 
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@procurement-agent.com"

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # Feature 1 — WhatsApp (Twilio)
    TWILIO_ACCOUNT_SID:    Optional[str] = None
    TWILIO_AUTH_TOKEN:     Optional[str] = None
    TWILIO_WHATSAPP_FROM:  Optional[str] = "whatsapp:+14155238886"
 
    # Feature 8 — Currency conversion
    EXCHANGE_RATE_API_KEY: Optional[str] = None


 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
settings = Settings()
 
