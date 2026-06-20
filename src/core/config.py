# src/core/config.py
import functools
from typing import Literal

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App metadata
    APP_NAME: str = "ChatOps Incident Agent"
    APP_ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = False

    # LLM API Keys
    GEMINI_API_KEY: SecretStr

    # Notification integrations
    DISCORD_WEBHOOK_URL: SecretStr | None = None

    # PostgreSQL connection parameters
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_NAME: str

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@functools.lru_cache()
def get_settings() -> Settings:
    return Settings()
