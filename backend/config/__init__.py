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
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/auditr",
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
    celery_task_always_eager: bool = Field(
        default=False,
        validation_alias="CELERY_TASK_ALWAYS_EAGER",
    )

    github_client_id: str = Field(default="", validation_alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", validation_alias="GITHUB_CLIENT_SECRET")
    github_webhook_secret: str = Field(default="dev-webhook-secret", validation_alias="GITHUB_WEBHOOK_SECRET")

    fernet_key: str = Field(default="", validation_alias="FERNET_KEY")

    github_oauth_redirect_uri: str = Field(
        default="http://127.0.0.1:8000/api/auth/github/callback",
        validation_alias="GITHUB_OAUTH_REDIRECT_URI",
    )
    auditr_domain: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias="AUDITR_DOMAIN",
    )

    frontend_oauth_success_url: str = Field(
        default="http://localhost:3000",
        validation_alias="FRONTEND_OAUTH_SUCCESS_URL",
    )

    jwt_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, validation_alias="JWT_EXPIRE_MINUTES")

    slack_bot_token: str = Field(default="", validation_alias="SLACK_BOT_TOKEN")
    slack_default_channel: str = Field(default="#general", validation_alias="SLACK_DEFAULT_CHANNEL")
    slack_client_id: str = Field(default="", validation_alias="SLACK_CLIENT_ID")
    slack_client_secret: str = Field(default="", validation_alias="SLACK_CLIENT_SECRET")
    slack_signing_secret: str = Field(default="", validation_alias="SLACK_SIGNING_SECRET")

    auditr_dashboard_base_url: str = Field(
        default="http://localhost:3000",
        validation_alias="AUDITR_DASHBOARD_URL",
    )
    api_public_base_url: str = Field(
        default="http://localhost:8000",
        validation_alias="API_PUBLIC_BASE_URL",
    )

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")

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
    celery_task_always_eager: bool = Field(
        default=True,
        validation_alias="CELERY_TASK_ALWAYS_EAGER",
    )


class TestSettings(BaseAppSettings):
    """Test environment — uses isolated DB by default when DATABASE_URL unset in tests."""

    environment: Literal["test"] = "test"
    database_url: str = "sqlite+aiosqlite:///:memory:"
    jwt_secret_key: str = "test-secret-key"
    celery_task_always_eager: bool = True


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
    try:
        from config.llm_config import clear_llm_config_cache

        clear_llm_config_cache()
    except ImportError:
        pass
