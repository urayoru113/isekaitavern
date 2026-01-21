import asyncio
import traceback
import typing
from collections import defaultdict

import beanie
import discord
import discord.ext.commands as commands
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import app_config
from .utils.extensions import get_name
from .utils.logging import logger


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        self.__prefix = app_config.bot.command_prefix

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix=commands.when_mentioned_or(app_config.bot.command_prefix), intents=intents)

        self._beanie_models_to_init: dict[AsyncIOMotorDatabase, list[type[beanie.Document]]] = defaultdict(list)
        self.__motor_client = AsyncIOMotorClient(app_config.database.mongo_url)
        logger.debug(f"start mongo client {self.__motor_client!r}")
        self.__redis_client = redis.Redis.from_url(app_config.database.redis_url, decode_responses=True)
        logger.debug(f"start redis client {self.__redis_client!r}")

    @typing.override
    async def setup_hook(self):
        if app_config.env == "dev":
            await self.load_extension("jishaku")

        cogs = [get_name(cog) for cog in app_config.bot.cogs]
        logger.info(f"load extensions: {cogs}")
        co_cogs = (self.load_extension(cog) for cog in cogs)
        await asyncio.gather(*co_cogs)

        beanie_init_tasks = (
            beanie.init_beanie(database, document_models=models)
            for database, models in self._beanie_models_to_init.items()
        )

        try:
            await self.redis.ping()
            await asyncio.gather(*beanie_init_tasks)
        except Exception as e:
            logger.error(f"Connection failed during startup: {e}")
            raise ConnectionError(e) from e

        if app_config.env == "dev":
            guild = discord.Object(id=app_config.dev.guild_id)
            self.tree.clear_commands(guild=guild)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        elif app_config.env == "prod":
            await self.tree.sync()

    @typing.override
    async def on_command_error(self, ctx: commands.Context, error: discord.DiscordException):
        error_message = "".join(traceback.format_exception(error))
        if app_config.env == "dev":
            error_message_python_highlight = f"```python\n{error_message}\n```"
            await ctx.send(error_message_python_highlight)
        logger.error(error_message)

    def _register_beanie_model(self, database: AsyncIOMotorDatabase, *models: type[beanie.Document]):
        for model in models:
            self._beanie_models_to_init[database].append(model)

    @staticmethod
    async def init_beanie(database: AsyncIOMotorDatabase, *models: type[beanie.Document]):
        await beanie.init_beanie(database, document_models=models)

    @property
    def prefix(self) -> str:
        return self.__prefix

    @property
    def redis(self) -> redis.Redis:
        return self.__redis_client

    @property
    def motor_client(self) -> AsyncIOMotorClient:
        return self.__motor_client
