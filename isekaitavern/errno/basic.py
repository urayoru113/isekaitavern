class ConfigException(Exception):
    def __init__(self, message: str = ""):
        self.message = f"{message} Please Check `config.toml` and `.env`."

    def __str__(self):
        return self.message
