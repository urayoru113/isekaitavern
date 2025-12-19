import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot

from ...config import app_config


class Echo(commands.Cog, name="echo"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx: commands.Context, *, message):
        await ctx.send(message)

    @commands.command()
    async def sync(self, ctx: commands.Context):
        assert app_config.env == "dev"
        guild = discord.Object(id=app_config.dev.guild_id)
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await ctx.send("Sync guild commands success")

    @commands.command()
    async def clear(self, ctx: commands.Context):
        assert app_config.env == "dev"
        guild = discord.Object(id=app_config.dev.guild_id)
        self.bot.tree.clear_commands(guild=ctx.guild)
        await self.bot.tree.sync(guild=guild)
        await ctx.send("Clear guild commands success")

    async def clear_global(self, ctx: commands.Context):
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await ctx.send("Clear global commands success")

    async def sync_global(self, ctx: commands.Context):
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await ctx.send("Sync global commands success")

    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("pong")

    @commands.command()
    async def reload(self, ctx: commands.Context, cog: str):
        cog = f"isekaitavern.cogs.{cog}.cog"
        if self.bot.get_cog(cog):
            await self.bot.unload_extension(cog)
        await self.bot.load_extension(cog)
        await ctx.send("Reload cog success")


async def setup(bot: DiscordBot):
    """Add echo cog."""
    await bot.add_cog(Echo(bot))
