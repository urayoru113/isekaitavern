import dataclasses
import os
import tomllib
from pathlib import Path
from typing import Literal

import dacite

from ..errno import ConfigException
from ..utils.helpers import dict_deep_extend


@dataclasses.dataclass
class Bot:
    token: str
    command_prefix: str
    command_colldown: int
    cogs: set[str]


@dataclasses.dataclass
class DatabaseConfig:
    mongo_url: str
    redis_url: str


@dataclasses.dataclass
class Log:
    name: str
    format: str
    colors: dict[str, str]


@dataclasses.dataclass
class Dev:
    guild_id: int


@dataclasses.dataclass
class DevConfig:
    bot: Bot
    database: DatabaseConfig
    log: Log
    env: Literal["dev"]
    dev: Dev

    def __post_init__(self):
        self.bot.cogs.add("debug")


@dataclasses.dataclass
class Config:
    bot: Bot
    database: DatabaseConfig
    log: Log
    env: Literal["test", "prod"]


def _load_settings() -> Config | DevConfig:
    with Path("config.toml").open("rb") as f:
        config = tomllib.load(f)

    env_config = {
        "bot": {"token": os.environ.get("DISCORD_BOT_TOKEN")},
        "database": {"mongo_url": os.environ.get("MONGO_URL"), "redis_url": os.environ.get("REDIS_URL")},
        "env": os.environ.get("ENV"),
    }
    if env_config["env"] == "dev":
        env_config.update({"dev": {"guild_id": os.environ.get("DEV_GUILD_ID")}})

    config = dict_deep_extend(config, env_config, strategy="error")

    try:
        data_class = DevConfig if env_config["env"] == "dev" else Config
        result = dacite.from_dict(data_class=data_class, data=config, config=dacite.Config(cast=[set, int]))
    except dacite.DaciteError as e:
        raise ConfigException(str(e)) from e

    return result


app_config = _load_settings()
