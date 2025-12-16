class TransmittableException(Exception):
    """Base class for all exceptions that can be transmitted to the user."""

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class ConfigException(Exception):
    def __init__(self, message: str = ""):
        self.message = f"{message} Please Check `config.toml` and `.env`."

    def __str__(self):
        return self.message
