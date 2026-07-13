import discord
from discord import app_commands
from discord.ext import commands

from ...bot import DiscordBot
from ...i18n import i18n
from ...services.channel import ChannelService
from ...utils.logging import logger


class ChannelCog(commands.Cog):
    """Channel management commands: create, delete, rename, category."""

    def __init__(self, bot: DiscordBot):
        logger.info("Initializing ChannelCog")
        self.bot = bot
        self.service = ChannelService()

    channel_group = app_commands.Group(
        name="channel",
        description="頻道管理",
        guild_only=True,
        default_permissions=discord.Permissions(manage_channels=True),
    )

    @channel_group.command(name="create", description="建立頻道")
    @app_commands.choices(
        channel_type=[
            app_commands.Choice(name="文字頻道", value="text"),
            app_commands.Choice(name="語音頻道", value="voice"),
            app_commands.Choice(name="分類頻道", value="category"),
        ]
    )
    async def channel_create(
        self,
        interaction: discord.Interaction,
        name: str,
        channel_type: app_commands.Choice[str],
        category: discord.CategoryChannel | None = None,
        reason: str | None = None,
    ):
        if interaction.guild is None:
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.invalid_state"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            channel = await self.service.create_channel(interaction.guild, name, channel_type.value, category, reason)
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.create_success", channel=channel.mention),
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.error", detail=str(e)),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @channel_group.command(name="category", description="建立分類頻道")
    async def channel_category(
        self,
        interaction: discord.Interaction,
        name: str,
        reason: str | None = None,
    ):
        if interaction.guild is None:
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.invalid_state"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            category = await self.service.create_category(interaction.guild, name, reason)
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.category_success", category=category.mention),
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.error", detail=str(e)),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @channel_group.command(name="delete", description="刪除頻道")
    async def channel_delete(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel,
        reason: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            channel_name = channel.name
            await self.service.delete_channel(channel, reason)
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.delete_success", name=channel_name),
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.error", detail=str(e)),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @channel_group.command(name="rename", description="重命名頻道")
    async def channel_rename(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel,
        new_name: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.service.rename_channel(channel, new_name)
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.rename_success", channel=channel.mention, name=new_name),
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=i18n.get_default("commands.channel.error", detail=str(e)),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: DiscordBot):
    cog = ChannelCog(bot)
    await bot.add_cog(cog)
