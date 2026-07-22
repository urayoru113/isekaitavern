import dataclasses
import os
import tomllib
from pathlib import Path
from typing import Literal

import dacite
import dotenv

from ..errno import ConfigException
from ..utils.helpers import dict_deep_extend


@dataclasses.dataclass
class Bot:
    token: str
    lang: str


@dataclasses.dataclass
class Agent:
    token: str
    base_url: str
    model: str


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
    log: Log
    env: Literal["dev"]
    dev: Dev
    agent: Agent


@dataclasses.dataclass
class Config:
    bot: Bot
    log: Log
    env: Literal["test", "prod"]
    agent: Agent


def _load_settings() -> Config | DevConfig:
    dotenv.load_dotenv()

    with Path("config.toml").open("rb") as f:
        config = tomllib.load(f)

    env_config = {
        "bot": {"token": os.environ.get("DISCORD_BOT_TOKEN")},
        "env": os.environ.get("ENV"),
        "agent": {
            "token": os.environ.get("PROVIDER_API_KEY"),
            "base_url": os.environ.get("LLM_BASE_URL"),
            "model": os.environ.get("LLM_MODEL"),
        },
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
