import asyncio
import os
import typing

import discord
import redis.asyncio as redis
from discord.ext import commands

from isekaitavern.config.redis import REDIS_URL
from isekaitavern.errno import TransmittableException
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

    @typing.override
    async def setup_hook(self):
        logger.info(f"bot prefix:{self.prefix}")
        cogs = [
            os.path.relpath(os.path.join(os.path.dirname(__file__), "cogs", folder, "cog.py")).replace("/", ".")
            for folder in os.listdir(os.path.join(os.path.dirname(__file__), "cogs"))
            if os.path.isdir(folder) and not folder.startswith("_")
        ]

        for folder in os.listdir(os.path.join(os.path.dirname(__file__), "cogs")):
            if os.path.isdir(folder) and not folder.startswith("_"):
                print(folder)
        co_cogs = [self.load_extension(cog) for cog in cogs]
        await asyncio.gather(*co_cogs)
        logger.info(f"extensions: {cogs}")

        try:
            self.redis = redis.Redis.from_url(REDIS_URL)
            await self.redis.ping()
            logger.info("Redis connection established")
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None
        except Exception as e:
            logger.error(e)
            self.redis = None

    @typing.override
    async def on_command_error(self, ctx: commands.Context, error: discord.DiscordException):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, TransmittableException):
            await ctx.send(*error.original.args)
        logger.error(*error.args)

    @property
    def prefix(self) -> str:
        return self.__prefix
