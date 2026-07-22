import dataclasses
import os
import tomllib
from pathlib import Path

import dacite
import dotenv

from ..errno import ConfigException
from ..utils.helpers import dict_deep_extend


@dataclasses.dataclass
class Bot:
    lang: str


@dataclasses.dataclass
class Agent:
    token: str
    base_url: str
    model: str


@dataclasses.dataclass
class Log:
    format: str


@dataclasses.dataclass
class AppConfig:
    bot: Bot
    log: Log
    agent: Agent


def _load_settings() -> AppConfig:
    dotenv.load_dotenv()

    with Path("config.toml").open("rb") as f:
        config = tomllib.load(f)

    env_config = {
        "bot": {"token": os.environ.get("DISCORD_BOT_TOKEN")},
        "agent": {
            "token": os.environ.get("PROVIDER_API_KEY"),
            "base_url": os.environ.get("LLM_BASE_URL"),
            "model": os.environ.get("LLM_MODEL"),
        },
    }

    config = dict_deep_extend(config, env_config, strategy="error")

    try:
        result = dacite.from_dict(data_class=AppConfig, data=config, config=dacite.Config(cast=[int]))
    except dacite.DaciteError as e:
        raise ConfigException(str(e)) from e

    return result


app_config = _load_settings()
