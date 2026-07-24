import tomllib
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Bot(BaseModel):
    model_config = ConfigDict(frozen=True)

    lang: str
    api: str
    model: str
    timezone: ZoneInfo
    allowed_guilds: list[int]

    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, value: str) -> ZoneInfo:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as e:
            raise ValueError(f"Invalid timezone: {value}") from e


class Log(BaseModel):
    model_config = ConfigDict(frozen=True)

    format: str


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    discord_bot_token: str

    agent_token: str
    agent_base_url: str

    search_endpoint: str


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    bot: Bot
    log: Log

    discord_bot_token: str
    search_endpoint: str
    agent_token: str
    agent_base_url: str


@lru_cache(1)
def load_settings() -> AppConfig:
    with Path("config.toml").open("rb") as f:
        config = tomllib.load(f)

    secrets = Secrets()  # pyright: ignore[reportCallIssue]
    config.update(secrets.model_dump())

    return AppConfig.model_validate(config)


app_config = load_settings()
