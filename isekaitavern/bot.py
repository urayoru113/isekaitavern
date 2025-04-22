import asyncio
import os
import typing
from collections import defaultdict

import beanie
import discord
import redis.asyncio as redis
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from isekaitavern.config.services import MONGO_HOST, REDIS_HOST
from isekaitavern.errno import TransmittableException
from isekaitavern.services.repository import RedisClient
from isekaitavern.utils.logging import logger


class DiscordBot(commands.Bot):
    def __init__(self, prefix: str) -> None:
        self.__prefix = prefix
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix),
            intents=intents,
        )

        self._beanie_models_to_init: dict[AsyncIOMotorDatabase, list[type[beanie.Document]]] = defaultdict(list)
        self.__motor_client = AsyncIOMotorClient(MONGO_HOST)
        self.__redis_client = RedisClient(redis.Redis.from_url(REDIS_HOST, decode_responses=True))

    @typing.override
    async def setup_hook(self):
        logger.info(f"bot prefix:{self.prefix}")

        cogs = []
        rel_dir = os.path.basename(os.path.dirname(__file__))
        for cog_dir in os.listdir(os.path.join(rel_dir, "cogs")):
            folder = os.path.join(rel_dir, "cogs", cog_dir)
            if os.path.isdir(folder) and not cog_dir.startswith("_"):
                cogs.append(os.path.join(folder, "cog").replace(os.path.sep, "."))
        co_cogs = (self.load_extension(cog) for cog in cogs)
        await asyncio.gather(*co_cogs)
        logger.info(f"extensions: {cogs}")

        beanie_init_tasks = (
            beanie.init_beanie(database, document_models=models)
            for database, models in self._beanie_models_to_init.items()
        )

        try:
            await self.__redis_client.redis.ping()
            await asyncio.gather(*beanie_init_tasks)
        except Exception as e:
            logger.critical(f"Connection failed during startup: {e}")

        await self.tree.sync()

    @typing.override
    async def on_command_error(self, ctx: commands.Context, error: discord.DiscordException):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, TransmittableException):
            await ctx.send(*error.original.args)
        logger.error(*error.args)

    def _register_beanie_model(self, database: AsyncIOMotorDatabase, *models: type[beanie.Document]):
        for model in models:
            self._beanie_models_to_init[database].append(model)

    @property
    def prefix(self) -> str:
        return self.__prefix

    @property
    def redis_client(self) -> RedisClient:
        return self.__redis_client

    @property
    def motor_client(self) -> AsyncIOMotorClient:
        return self.__motor_client
