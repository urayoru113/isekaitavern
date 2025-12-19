import discord

from .model import AnonymousBaseSettings, AnonymousUserSettings


class AnonymousService:
    """Business logic for anonymous messaging system"""

    @staticmethod
    def build_config_embed(config: AnonymousBaseSettings) -> discord.Embed:
        embed = discord.Embed(
            title="Anonymous Configuration",
            color=discord.Color.blue() if config.enabled else discord.Color.light_grey(),
        )

        status = "✅ Enabled" if config.enabled else "❌ Disabled"
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Cooldown", value=f"{config.cooldown_seconds}s", inline=True)

        channels_text = "\n".join(f"<#{ch_id}>" for ch_id in config.channel_ids) if config.channel_ids else "None"
        embed.add_field(name="Channels", value=channels_text, inline=False)

        blocked_text = "\n".join(f"<@{u_id}>" for u_id in config.blocked_users) if config.blocked_users else "None"
        embed.add_field(name="Blocked Users", value=blocked_text, inline=False)

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
        embed = discord.Embed(description="test")
        embed.set_author(name=user_settings.display_name, icon_url=user_settings.avatar_url)
        return embed
