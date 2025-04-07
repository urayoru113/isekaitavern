import os

import dotenv

dotenv.load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")

if not DISCORD_BOT_TOKEN:
    raise ValueError("`DISCORD_BOT_TOKEN` is empty")

if not COMMAND_PREFIX:
    raise ValueError("`COMMAND_PREFIX` is empty")
