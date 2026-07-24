from isekaitavern.bot import DiscordBot
from isekaitavern.config import app_config

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(app_config.discord_bot_token, log_handler=None)
