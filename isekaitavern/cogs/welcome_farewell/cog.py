import typing

import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.services.repository import RedisClient
from isekaitavern.utils.context_helper import fetch_guild, fetch_member

from . import WelcomeFareWellModel
from .core import WelcomeFarewell


class WelcomeFarewellCog(commands.Cog, name="greeting"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.bot._register_beanie_model(self.bot.motor_client.GuildSettings, WelcomeFareWellModel)
        self.guild_client = WelcomeFarewell(self.redis_client)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        channel = member.guild.system_channel
        if not channel:
            return

        welcome_msg = await self.guild_client.get_welcome_msg(member)

        if not welcome_msg:
            return

        await channel.send(welcome_msg)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        channel = member.guild.system_channel
        if not channel:
            return

        farewell_msg = await self.guild_client.get_farewell_msg(member)

        if not farewell_msg:
            return

        await channel.send(farewell_msg)

    @commands.command()
    async def set_welcome_msg(self, ctx: commands.Context, *, msg: str = ""):
        guild = fetch_guild(ctx)
        member = fetch_member(ctx)
        await self.guild_client.set_welcome_msg(guild, member, msg)
        await ctx.send("Updated welcome message successfully")

    @commands.command()
    async def set_remove_msg(self, ctx: commands.Context, *, msg: str = ""):
        guild = fetch_guild(ctx)
        member = fetch_member(ctx)
        await self.guild_client.set_farewell_msg(guild, member, msg)
        await ctx.send("Updated farewell message successfully")

    @property
    def redis_client(self) -> RedisClient:
        assert self.bot.redis_client, "Redis client is not initialized"
        return self.bot.redis_client

    @typing.override
    async def cog_check(self, ctx: commands.Context) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self.bot.redis_client:
            await ctx.send("Storage is not available, please try again later")
            return False

        if not ctx.guild:
            await ctx.send("This command can only be used in a server")
            return False

        return True


async def setup(bot: DiscordBot):
    """Add greeting cog."""
    await bot.add_cog(WelcomeFarewellCog(bot))
