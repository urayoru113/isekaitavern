import os

import dotenv

from isekaitavern.bot import DiscordBot

if __name__ == "__main__":
    dotenv.load_dotenv()

    discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
    command_prefix = os.getenv("COMMAND_PREFIX")

    if not command_prefix:
        raise ValueError("`COMMAND_PREFIX` is empty")
    if not discord_bot_token:
        raise ValueError("`DISCORD_BOT_TOKEN` is empty")
    bot = DiscordBot(command_prefix)
    bot.run(discord_bot_token)
