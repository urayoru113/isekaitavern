import logging

from ..config.settings import app_config


def _get_logger():
    logging.basicConfig(format=app_config.log.format, datefmt="%Y-%m-%d %H:%M:%S")

    logger = logging.getLogger(app_config.log.name)
    if app_config.env == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


logger = _get_logger()
