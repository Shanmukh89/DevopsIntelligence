"""Application configuration via Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Shared settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "test", "prod"] = Field(
        default="dev",
        validation_alias="ENVIRONMENT",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        validation_alias="DATABASE_URL",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_async_database_url(cls, v: object) -> object:
        """Use async drivers: postgresql:// -> postgresql+asyncpg://"""
        if not isinstance(v, str):
            return v
        if v.startswith("postgresql://") and "+asyncpg" not in v and "+psycopg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )

    github_client_id: str = Field(default="", validation_alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", validation_alias="GITHUB_CLIENT_SECRET")
    github_webhook_secret: str = Field(default="dev-webhook-secret", validation_alias="GITHUB_WEBHOOK_SECRET")

    jwt_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, validation_alias="JWT_EXPIRE_MINUTES")

    slack_bot_token: str = Field(default="", validation_alias="SLACK_BOT_TOKEN")
    slack_default_channel: str = Field(default="#general", validation_alias="SLACK_DEFAULT_CHANNEL")

    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


class DevSettings(BaseAppSettings):
    """Development defaults."""

    environment: Literal["dev"] = "dev"


class TestSettings(BaseAppSettings):
    """Test environment — uses isolated DB by default when DATABASE_URL unset in tests."""

    environment: Literal["test"] = "test"
    database_url: str = "sqlite+aiosqlite:///:memory:"
    jwt_secret_key: str = "test-secret-key"


class ProdSettings(BaseAppSettings):
    """Production — stricter expectations."""

    environment: Literal["prod"] = "prod"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def jwt_must_be_secure_in_prod(self) -> "ProdSettings":
        if self.jwt_secret_key.startswith("change-me"):
            msg = "JWT_SECRET_KEY must be set to a secure value in production"
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> BaseAppSettings:
    """Return cached settings instance; validates on first access."""
    import os

    env = os.getenv("ENVIRONMENT", "dev").lower()
    if env == "prod":
        return ProdSettings()
    if env == "test":
        return TestSettings()
    return DevSettings()


def clear_settings_cache() -> None:
    """Clear settings cache (for tests)."""
    get_settings.cache_clear()
