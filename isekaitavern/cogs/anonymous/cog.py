import discord
from discord import app_commands
from discord.ext import commands

from isekaitavern.bot import DiscordBot

from ... import i18n
from ...utils.logging import logger
from .model import AnonymousBaseSettings, AnonymousUserSettings
from .repository import AnonymousRepository
from .services import AnonymousService


class AnonymousCog(commands.Cog, name="anonymous"):
    def __init__(self, bot: DiscordBot) -> None:
        logger.info("Initializing AnonymousCog")
        self.bot = bot
        self.repo = AnonymousRepository(self.bot.redis)
        self.service = AnonymousService()

    async def cog_load(self):
        await self.bot.init_beanie(self.bot.motor_client.db, AnonymousBaseSettings)

    # Create command group
    anonymous = app_commands.Group(name="anonymous", description="Anonymous messaging system")

    # ========================================
    # Admin Commands
    # ========================================
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="enable", description="Enable anonymous feature")
    async def anonymous_enable(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        await self.repo.set_base_settings_model(guild_id=interaction.guild.id, enabled=True)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.anonymous.enabled"))

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="disable", description="Disable anonymous feature")
    async def anonymous_disable(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        await self.repo.set_base_settings_model(guild_id=interaction.guild.id, enabled=False)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.anonymous.disabled"))

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="add_channel", description="Add a channel for anonymous messages")
    async def anonymous_add_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        assert interaction.guild is not None
        await self.repo.add_channel(guild_id=interaction.guild.id, channel_id=channel.id)
        await interaction.response.send_message(
            i18n.get("zh-tw", "commands.anonymous.add_channel", channel=channel.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="del_channel", description="Remove a channel from anonymous messages")
    async def anonymous_del_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        assert interaction.guild is not None
        await self.repo.remove_channel(guild_id=interaction.guild.id, channel_id=channel.id)
        await interaction.response.send_message(
            i18n.get("zh-tw", "commands.anonymous.remove_channel", channel=channel.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="cooldown", description="Set cooldown time in seconds")
    async def anonymous_cooldown(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 1, 300]):
        assert interaction.guild is not None
        await self.repo.set_base_settings_model(guild_id=interaction.guild.id, cooldown_seconds=seconds)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.anonymous.cooldown_set", seconds=seconds))

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="block", description="Block a user from using anonymous feature")
    async def anonymous_block(self, interaction: discord.Interaction, member: discord.Member):
        assert interaction.guild is not None
        await self.repo.block_user(guild_id=interaction.guild.id, user_id=member.id)
        await interaction.response.send_message(
            i18n.get("zh-tw", "commands.anonymous.user_blocked", user=member.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="unblock", description="Unblock a user from anonymous feature")
    async def anonymous_unblock(self, interaction: discord.Interaction, member: discord.Member):
        assert interaction.guild is not None
        await self.repo.unblock_user(guild_id=interaction.guild.id, user_id=member.id)
        await interaction.response.send_message(
            i18n.get("zh-tw", "commands.anonymous.user_unblocked", user=member.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="config", description="View anonymous feature configuration")
    async def anonymous_config(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        config_model = await self.repo.get_base_settings_model(guild_id=interaction.guild.id)
        if not config_model:
            await self.repo.set_base_settings_model(guild_id=interaction.guild.id)
            config_model = AnonymousBaseSettings(guild_id=interaction.guild.id)
        embed = self.service.build_config_embed(config_model)
        await interaction.response.send_message(embed=embed)

    # ========================================
    # User Commands
    # ========================================

    @app_commands.guild_only()
    @anonymous.command(name="icon", description="Set your anonymous avatar URL")
    async def anonymous_icon(self, interaction: discord.Interaction, icon: str):
        assert interaction.guild is not None
        # TODO:validate url
        await self.repo.set_user_settings_model(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            avatar_url=icon,
        )
        await interaction.response.send_message(i18n.get("zh-tw", "commands.anonymous.icon_set"), ephemeral=True)

    @app_commands.guild_only()
    @anonymous.command(name="name", description="Set your anonymous display name")
    async def anonymous_name(self, interaction: discord.Interaction, name: app_commands.Range[str, 1, 32]):
        assert interaction.guild is not None
        await self.repo.set_user_settings_model(
            guild_id=interaction.guild.id, user_id=interaction.user.id, display_name=name
        )
        await interaction.response.send_message(
            i18n.get("zh-tw", "commands.anonymous.name_set", name=name), ephemeral=True
        )

    @app_commands.guild_only()
    @anonymous.command(name="preivew", description="Preview your anonymous settings")
    async def anonymous_preview(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        model = await self.repo.get_user_settings_model(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not model:
            await self.repo.set_user_settings_model(guild_id=interaction.guild.id, user_id=interaction.user.id)
            model = AnonymousUserSettings(guild_id=interaction.guild.id, user_id=interaction.user.id)
        embed = self.service.build_preview(model)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.guild_only()
    @anonymous.command(name="send", description="Send an anonymous message")
    async def anonymous_send(self, interaction: discord.Interaction, message: app_commands.Range[str, 1, 2000]):
        assert interaction.guild is not None
        assert isinstance(interaction.channel, discord.TextChannel)
        await interaction.response.defer(ephemeral=True)

        # Check if current channel is in anonymous channels
        base_settings = await self.repo.get_base_settings_model(interaction.guild.id)
        if not base_settings or interaction.channel.id not in base_settings.channel_ids:
            await interaction.followup.send(i18n.get("zh-tw", "commands.anonymous.not_a_channel"), ephemeral=True)
            return

        # Get user settings
        user_settings = await self.repo.get_user_settings_model(interaction.guild.id, interaction.user.id)
        if not user_settings:
            user_settings = await self.repo.set_user_settings_model(
                guild_id=interaction.guild.id, user_id=interaction.user.id
            )
            user_settings = AnonymousUserSettings(guild_id=interaction.guild.id, user_id=interaction.user.id)

        # Build webhook payload
        webhook_payload = AnonymousService.build_webhook_payload(user_settings, message)

        # Create webhook
        webhook = await interaction.channel.create_webhook(name="Anonymous Webhook")
        try:
            # Send message
            await webhook.send(
                content=webhook_payload["content"],
                username=webhook_payload["username"],
                avatar_url=webhook_payload["avatar_url"],
            )
        finally:
            # Delete webhook
            await webhook.delete()

        await interaction.followup.send(i18n.get("zh-tw", "commands.anonymous.message_sent"), ephemeral=True)


async def setup(bot: DiscordBot):
    await bot.add_cog(AnonymousCog(bot))
