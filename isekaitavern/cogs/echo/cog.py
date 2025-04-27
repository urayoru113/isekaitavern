import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.utils.context_helper import fetch_guild


class Echo(commands.Cog, name="echo"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx: commands.Context, *, message):
        await ctx.send(message)

    @commands.command()
    async def sync(self, ctx: commands.Context):
        guild = fetch_guild(ctx)
        await self.bot.tree.sync(guild=discord.Object(id=guild.id))
        await ctx.send(f"sync {guild.name}")

    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("pong")


async def setup(bot: DiscordBot):
    """Add echo cog."""
    await bot.add_cog(Echo(bot))
