from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App config
    PROJECT_NAME: str = "Auditr API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    # Format: postgresql://user:password@server/db
    SUPABASE_DB_URL: Optional[str] = None
    
    # GitHub Webhook Authentication
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY_PATH: Optional[str] = None

    # AI Providers
    OPENAI_API_KEY: Optional[str] = None

    # Slack Integrations
    SLACK_BOT_TOKEN: Optional[str] = None

    # Celery Redis Broker
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
