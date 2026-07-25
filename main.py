from isekaitavern.bot import DiscordBot
from isekaitavern.config import app_config
from isekaitavern.utils.log import DEFAULT_LOGGER_NAME, get_logger, setup_logging

if __name__ == "__main__":
    setup_logging(DEFAULT_LOGGER_NAME)
    setup_logging("assistant_core")
    logger = get_logger(DEFAULT_LOGGER_NAME)

    bot = DiscordBot()
    bot.run(app_config.discord_bot_token, log_handler=logger.handlers[0])
