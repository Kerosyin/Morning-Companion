from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_id: int = Field(alias="ADMIN_ID")

    ai_provider: str = Field(default="openrouter", alias="AI_PROVIDER")
    model: str = Field(alias="MODEL")
    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")

    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    database_url: str = Field(alias="DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
