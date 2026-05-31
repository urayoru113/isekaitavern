from urllib.parse import urlparse

import discord

from isekaitavern.bot import DiscordBot

from ... import i18n
from .model import AnonymousBaseSettings, AnonymousUserSettings, AnonymousWebhookInfo
from .repository import AnonymousRepository


class AnonymousService:
    """Business logic for anonymous messaging system"""

    def __init__(self, repo: AnonymousRepository):
        self.repo = repo

    @staticmethod
    def validate_avatar_url(url: str) -> bool:
        """Validate that the URL is a well-formed HTTP(S) URL."""

        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @staticmethod
    def build_config_embed(
        config: AnonymousBaseSettings, webhook_infos: list[AnonymousWebhookInfo] | None = None
    ) -> discord.Embed:
        embed = discord.Embed(
            title=i18n.get_default("commands.anonymous.config_title"),
            color=discord.Color.blue() if config.enabled else discord.Color.light_grey(),
        )

        status = (
            i18n.get_default("commands.anonymous.status_enabled")
            if config.enabled
            else i18n.get_default("commands.anonymous.status_disabled")
        )
        embed.add_field(name=i18n.get_default("commands.anonymous.config_status"), value=status, inline=True)
        embed.add_field(
            name=i18n.get_default("commands.anonymous.config_cooldown"),
            value=f"{config.cooldown_seconds}s",
            inline=True,
        )

        anonymous_none_text = i18n.get_default("commands.anonymous.none")
        channels_text = (
            "\n".join(f"<#{webhook_infos.channel_id}>" for webhook_infos in webhook_infos)
            if webhook_infos
            else anonymous_none_text
        )
        embed.add_field(name=i18n.get_default("commands.anonymous.config_channels"), value=channels_text, inline=False)

        blocked_text = (
            "\n".join(f"<@{u_id}>" for u_id in config.blocked_users) if config.blocked_users else anonymous_none_text
        )
        embed.add_field(name=i18n.get_default("commands.anonymous.config_blocked"), value=blocked_text, inline=False)

        return embed

    @staticmethod
    def build_webhook_payload(user_settings: AnonymousUserSettings, content: str) -> dict:
        return {
            "username": user_settings.display_name,
            "avatar_url": user_settings.avatar_url or None,
            "content": content,
        }

    @staticmethod
    def build_preview(user_settings: AnonymousUserSettings) -> discord.Embed:
        embed = discord.Embed(description=i18n.get_default("commands.anonymous.preview_title"))
        embed.set_author(name=user_settings.display_name, icon_url=user_settings.avatar_url)
        return embed

    async def add_channel(self, guild_id: int, channel: discord.TextChannel) -> None:
        """Add a channel to anonymous channel list"""
        webhook = None
        try:
            webhook = await channel.create_webhook(name="Anonymous Webhook")
            assert webhook.token is not None, "Webhook created but no token was found."
            await self.repo.add_webhook_info(
                guild_id=guild_id, channel_id=channel.id, webhook_id=webhook.id, webhook_token=webhook.token
            )
        except Exception as e:
            if webhook:
                await webhook.delete()
            raise ValueError(f"Failed to add channel: {e}") from e

    async def remove_channel(self, channel: discord.TextChannel) -> None:
        """remove a channel from anonymous channel list"""
        webhook_info = await self.repo.get_webhook_info(channel_id=channel.id)
        if webhook_info:
            for webhook in await channel.webhooks():
                if webhook.id == webhook_info.webhook_id:
                    await webhook.delete()
                    break

        await self.repo.remove_webhook_info(channel.id)

    async def get_webhook(self, bot: DiscordBot, channel: discord.TextChannel) -> discord.Webhook | None:
        webhook_auth = await self.repo.get_webhook_info(channel.id)
        if not webhook_auth:
            return None
        return discord.Webhook.partial(id=webhook_auth.webhook_id, token=webhook_auth.webhook_token, client=bot)

    async def get_guild_all_webhook_infos(self, guild_id: int) -> list[AnonymousWebhookInfo]:
        webhook_infos = await self.repo.get_all_webhook_infos(guild_id=guild_id)
        return webhook_infos
