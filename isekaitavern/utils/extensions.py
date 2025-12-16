from pathlib import Path

from ..config import app_config


def get_name(cog: str) -> str:
    if cog not in app_config.bot.cogs:
        raise ValueError(f"Cog {cog} not found in `config.toml`")
    if not Path(f"isekaitavern/cogs/{cog}").is_dir():
        raise NotADirectoryError(f"Cog directory cogs/{cog} not found")
    if not Path(f"isekaitavern/cogs/{cog}/cog.py").is_file():
        raise FileNotFoundError(f"Cog file cogs/{cog}/cog.py not found")
    return f"isekaitavern.cogs.{cog}.cog"
