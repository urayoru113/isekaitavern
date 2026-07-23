import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Bot(BaseModel):
    model_config = ConfigDict(frozen=True)

    lang: Literal["en", "zh-TW"]
    allowed_guilds: list[int]


class Log(BaseModel):
    model_config = ConfigDict(frozen=True)

    format: str


class Agent(BaseModel):
    model_config = ConfigDict(frozen=True)

    token: str
    base_url: str
    model: str


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    discord_bot_token: str

    agent_token: str
    agent_base_url: str
    agent_model: str


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    agent: Agent
    bot: Bot
    log: Log


@lru_cache(1)
def load_settings() -> AppConfig:
    with Path("config.toml").open("rb") as f:
        config = tomllib.load(f)

    secrets = Secrets()  # pyright: ignore[reportCallIssue]

    config["agent"] = {
        "token": secrets.agent_token,
        "base_url": secrets.agent_base_url,
        "model": secrets.agent_model,
    }

    return AppConfig.model_validate(config)


app_config = load_settings()
