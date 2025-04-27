import asyncio
import os
import typing
from collections import defaultdict
from glob import glob

import aiohttp
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
        self.__aiohttp_session: aiohttp.ClientSession | None = None

    @typing.override
    async def setup_hook(self):
        logger.info(f"bot prefix:{self.prefix}")

        self.__aiohttp_session = aiohttp.ClientSession()

        cogs = [
            file[:-3].replace(os.path.sep, ".")
            for file in glob("isekaitavern/cogs/**/cog.py", recursive=True)
            if os.path.isfile(file)
        ]
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
            raise ConnectionError(e) from e

    @typing.override
    async def on_command_error(self, ctx: commands.Context, error: discord.DiscordException):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, TransmittableException):
            await ctx.send(*error.original.args)
        logger.error(*error.args)

    @typing.override
    async def close(self):
        if self.__aiohttp_session:
            await self.__aiohttp_session.close()
        await super().close()

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

    @property
    def aiohttp_session(self) -> aiohttp.ClientSession:
        assert self.__aiohttp_session, "Session not initialized"
        return self.__aiohttp_session
