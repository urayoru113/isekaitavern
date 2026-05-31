import discord
from discord import app_commands
from discord.ext import commands

from isekaitavern.bot import DiscordBot

from ... import i18n
from ...constants import MAX_WEBHOOK_SIZE
from ...utils.logging import logger
from .model import AnonymousBaseSettings, AnonymousUserSettings, AnonymousWebhookInfo
from .repository import AnonymousRepository
from .services import AnonymousService


class AnonymousCog(commands.Cog, name="anonymous"):
    def __init__(self, bot: DiscordBot) -> None:
        logger.info("Initializing AnonymousCog")
        self.bot = bot
        self.repo = AnonymousRepository(self.bot.redis)
        self.service = AnonymousService(self.repo)

        self._db = self.bot.motor_client.GuildSettings
        self._models = {AnonymousBaseSettings, AnonymousUserSettings, AnonymousWebhookInfo}

        self.bot._register_beanie_model(
            self.bot.motor_client.GuildSettings,
            AnonymousBaseSettings,
            AnonymousUserSettings,
            AnonymousWebhookInfo,
        )

    # Create command group
    anonymous = app_commands.Group(name="anonymous", description="Anonymous messaging system")

    # ========================================
    # Admin Commands
    # ========================================
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="enable", description="Enable anonymous feature")
    async def anonymous_enable(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return

        await self.repo.set_base_settings_model(guild_id=interaction.guild.id, enabled=True)
        await interaction.response.send_message(i18n.get_default("commands.anonymous.enabled"), ephemeral=True)

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="disable", description="Disable anonymous feature")
    async def anonymous_disable(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return

        await self.repo.set_base_settings_model(guild_id=interaction.guild.id, enabled=False)
        await interaction.response.send_message(i18n.get_default("commands.anonymous.disabled"))

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="add_channel", description="Add a channel for anonymous messages")
    async def anonymous_add_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None:
            return

        if len(await channel.webhooks()) >= MAX_WEBHOOK_SIZE:
            await interaction.response.send_message(i18n.get_default("errors.out_of_webhooks"), ephemeral=True)
            return
        webhook = await self.service.get_webhook(self.bot, channel)
        if webhook:
            await interaction.response.send_message(
                i18n.get_default("commands.anonymous.already_exists", channel=channel.mention)
            )
            return
        await self.service.add_channel(guild_id=interaction.guild.id, channel=channel)
        await interaction.response.send_message(
            i18n.get_default("commands.anonymous.add_channel", channel=channel.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="del_channel", description="Remove a channel from anonymous messages")
    async def anonymous_del_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None:
            return

        await self.service.remove_channel(channel=channel)
        await interaction.response.send_message(
            i18n.get_default("commands.anonymous.remove_channel", channel=channel.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="cooldown", description="Set anonymous message cooldown time in seconds")
    async def anonymous_cooldown(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 1, 300]):
        if interaction.guild is None:
            return

        await self.repo.set_base_settings_model(guild_id=interaction.guild.id, cooldown_seconds=seconds)
        await interaction.response.send_message(i18n.get_default("commands.anonymous.cooldown_set", seconds=seconds))

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="block", description="Block a user from using anonymous feature")
    async def anonymous_block(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.guild is None:
            return

        await self.repo.block_user(guild_id=interaction.guild.id, user_id=member.id)
        await interaction.response.send_message(
            i18n.get_default("commands.anonymous.user_blocked", user=member.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="unblock", description="Unblock a user from anonymous feature")
    async def anonymous_unblock(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.guild is None:
            return

        await self.repo.unblock_user(guild_id=interaction.guild.id, user_id=member.id)
        await interaction.response.send_message(
            i18n.get_default("commands.anonymous.user_unblocked", user=member.mention)
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @anonymous.command(name="config", description="View anonymous feature configuration")
    async def anonymous_config(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return

        config_model = await self.repo.get_base_settings_model(guild_id=interaction.guild.id)
        if not config_model:
            await self.repo.set_base_settings_model(guild_id=interaction.guild.id)
            config_model = AnonymousBaseSettings(guild_id=interaction.guild.id)
        webhook_infos = await self.repo.get_all_webhook_infos(guild_id=interaction.guild.id)
        embed = self.service.build_config_embed(config_model, webhook_infos=webhook_infos)
        await interaction.response.send_message(embed=embed)

    # ========================================
    # User Commands
    # ========================================

    @app_commands.guild_only()
    @anonymous.command(name="icon", description="Set your anonymous avatar URL")
    async def anonymous_icon(self, interaction: discord.Interaction, icon: str):
        if interaction.guild is None:
            return

        if not self.service.validate_avatar_url(icon):
            await interaction.response.send_message(
                i18n.get_default("errors.invalid_url"),
                ephemeral=True,
            )
            return

        await self.repo.set_user_settings_model(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            avatar_url=icon,
        )
        await interaction.response.send_message(i18n.get_default("commands.anonymous.icon_set"), ephemeral=True)

    @app_commands.guild_only()
    @anonymous.command(name="name", description="Set your anonymous display name")
    async def anonymous_name(self, interaction: discord.Interaction, name: app_commands.Range[str, 1, 32]):
        if interaction.guild is None:
            return

        await self.repo.set_user_settings_model(
            guild_id=interaction.guild.id, user_id=interaction.user.id, display_name=name
        )
        await interaction.response.send_message(
            i18n.get_default("commands.anonymous.name_set", name=name), ephemeral=True
        )

    @app_commands.guild_only()
    @anonymous.command(name="preview", description="Preview your anonymous settings")
    async def anonymous_preview(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return

        model = await self.repo.get_user_settings_model(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not model:
            await self.repo.set_user_settings_model(guild_id=interaction.guild.id, user_id=interaction.user.id)
            model = AnonymousUserSettings(guild_id=interaction.guild.id, user_id=interaction.user.id)
        embed = self.service.build_preview(model)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.guild_only()
    @anonymous.command(name="send", description="Send an anonymous message")
    async def anonymous_send(self, interaction: discord.Interaction, message: app_commands.Range[str, 1, 2000]):
        if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
            return

        await interaction.response.defer(ephemeral=True)

        base_settings = await self.repo.get_base_settings_model(interaction.guild.id)
        error_message: str | None = None

        if not base_settings:
            error_message = i18n.get_default("commands.anonymous.feature_disabled")
        else:
            if not base_settings.enabled:
                error_message = i18n.get_default("commands.anonymous.feature_disabled")
            if interaction.user.id in base_settings.blocked_users:
                error_message = i18n.get_default("commands.anonymous.you_are_blocked")

        if error_message:
            await interaction.followup.send(error_message, ephemeral=True)
            return

        user_settings = await self.repo.get_user_settings_model(interaction.guild.id, interaction.user.id)
        if not user_settings:
            await self.repo.set_user_settings_model(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
            )
            user_settings = AnonymousUserSettings(guild_id=interaction.guild.id, user_id=interaction.user.id)

        webhook_payload = AnonymousService.build_webhook_payload(user_settings, message)
        webhook = await self.service.get_webhook(self.bot, interaction.channel)
        if not webhook:
            await interaction.followup.send(i18n.get_default("commands.anonymous.webhook_error"), ephemeral=True)
            return

        try:
            await webhook.send(
                content=webhook_payload["content"],
                username=webhook_payload["username"],
                avatar_url=webhook_payload["avatar_url"],
            )
        except discord.DiscordException:
            await interaction.followup.send(i18n.get_default("commands.anonymous.webhook_error"), ephemeral=True)

        await interaction.followup.send(i18n.get_default("commands.anonymous.message_sent"), ephemeral=True)


async def setup(bot: DiscordBot):
    await bot.add_cog(AnonymousCog(bot))
