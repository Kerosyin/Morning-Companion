from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_id: int = Field(alias="ADMIN_ID")

    proxy: str | None = Field(default=None, alias="PROXY")

    ai_provider: str = Field(default="openrouter", alias="AI_PROVIDER")
    model: str = Field(alias="MODEL")
    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    ai_request_timeout_seconds: int = Field(
        default=30, alias="AI_REQUEST_TIMEOUT_SECONDS"
    )

    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    database_url: str = Field(alias="DATABASE_URL")

    message_retention_days: int = Field(default=365, alias="MESSAGE_RETENTION_DAYS")

    critical_alert_enabled: bool = Field(default=True, alias="CRITICAL_ALERT_ENABLED")
    critical_alert_min_severity: str = Field(
        default="high", alias="CRITICAL_ALERT_MIN_SEVERITY"
    )
    critical_alert_cooldown_minutes: int = Field(
        default=120, alias="CRITICAL_ALERT_COOLDOWN_MINUTES"
    )

    allowed_users: Annotated[list[int], NoDecode] = Field(
        default_factory=list, alias="ALLOWED_USERS"
    )

    @field_validator("allowed_users", mode="before")
    @classmethod
    def split_allowed_users(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
