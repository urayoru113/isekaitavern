import os

import dotenv
from dotenv import load_dotenv

from isekaitavern.bot import DiscordBot

if __name__ == "__main__":
    load_dotenv()
    dotenv.load_dotenv()

    discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if not discord_bot_token:
        raise ValueError("`DISCORD_BOT_TOKEN` is empty")

    bot = DiscordBot()
    bot.run(discord_bot_token, log_handler=None)
