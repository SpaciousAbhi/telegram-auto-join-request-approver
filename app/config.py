from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    owner_id: int = Field(..., alias="OWNER_ID")
    mongo_db_uri: str = Field(..., alias="MONGO_DB_URI")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("bot_token", "mongo_db_uri")
    @classmethod
    def reject_placeholders(cls, value: str) -> str:
        value = value.strip()
        if not value or value.startswith("YOUR_"):
            raise ValueError("Required environment variable is missing or still uses a placeholder.")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
