import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..config.settings import app_config

DEFAULT_LOGGER_NAME = "isekaitavern"

_DEFAULT_SAVE_DIR = "logs"


def setup_logging(logger_name: str = DEFAULT_LOGGER_NAME) -> None:
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt=app_config.log.format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(app_config.log.level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_path = Path(_DEFAULT_SAVE_DIR) / f"{DEFAULT_LOGGER_NAME}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file.setLevel(logging.DEBUG)
    file.setFormatter(formatter)
    logger.addHandler(file)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
