import discord
from discord import app_commands
from discord.ext import commands

from isekaitavern.bot import DiscordBot

from ...config import app_config


class DebugCog(commands.Cog, name="debug"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    debug = app_commands.Group(name="debug", description="Debug utilities (dev only)")

    @debug.command(name="echo", description="Echo back a message")
    async def debug_echo(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

    @debug.command(name="sync", description="Sync guild commands")
    @app_commands.guild_only()
    async def debug_sync(self, interaction: discord.Interaction):
        if app_config.env != "dev":
            await interaction.response.send_message("This command can only be used in dev environment", ephemeral=True)
            return
        if interaction.guild is None:
            return
        guild = discord.Object(id=interaction.guild.id)
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await interaction.response.send_message("Sync guild commands success", ephemeral=True)

    @debug.command(name="clear", description="Clear guild commands")
    @app_commands.guild_only()
    async def debug_clear(self, interaction: discord.Interaction):
        if app_config.env != "dev":
            await interaction.response.send_message("This command can only be used in dev environment", ephemeral=True)
            return
        if interaction.guild is None:
            return
        guild = discord.Object(id=interaction.guild.id)
        self.bot.tree.clear_commands(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await interaction.response.send_message("Clear guild commands success", ephemeral=True)

    @debug.command(name="clear_global", description="Clear global commands")
    async def debug_clear_global(self, interaction: discord.Interaction):
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await interaction.response.send_message("Clear global commands success", ephemeral=True)

    @debug.command(name="sync_global", description="Sync global commands")
    async def debug_sync_global(self, interaction: discord.Interaction):
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await interaction.response.send_message("Sync global commands success", ephemeral=True)

    @debug.command(name="ping", description="Pong!")
    async def debug_ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("pong")

    @debug.command(name="reload", description="Reload a cog extension")
    async def debug_reload(self, interaction: discord.Interaction, cog: str):
        cog_path = f"isekaitavern.cogs.{cog}.cog"
        await self.bot.unload_extension(cog_path)
        await self.bot.load_extension(cog_path)
        await interaction.response.send_message("Reload cog success", ephemeral=True)


async def setup(bot: DiscordBot):
    """Add debug cog."""
    await bot.add_cog(DebugCog(bot))
