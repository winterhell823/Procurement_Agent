from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    #Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/procurement"

    #Auth
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # TnyFish
    TINYFISH_API_KEY: str = ""
    TINYFISH_BASE_URL: str = "https://api.tinyfish.ai"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
 
    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@procurement-agent.com"
 
    class Config:
        env_file = ".env"
 
settings = Settings()
 
