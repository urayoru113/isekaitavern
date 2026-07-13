import datetime

import discord

from ..i18n import i18n
from ..utils.logging import logger


class ChannelService:
    """Business logic for channel management: create, delete, rename."""

    async def create_category(
        self,
        guild: discord.Guild,
        name: str,
        reason: str | None = None,
    ) -> discord.CategoryChannel:
        return await guild.create_category(name, reason=reason)

    async def create_channel(
        self,
        guild: discord.Guild,
        name: str,
        channel_type: str,
        category: discord.CategoryChannel | None = None,
        reason: str | None = None,
    ) -> discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel:
        if channel_type == "text":
            return await guild.create_text_channel(name, category=category, reason=reason)
        if channel_type == "voice":
            return await guild.create_voice_channel(name, category=category, reason=reason)
        if channel_type == "category":
            return await self.create_category(guild, name, reason)
        raise ValueError(i18n.get_default("commands.channel.unknown_type", type=channel_type))

    async def delete_channel(
        self,
        channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel,
        reason: str | None = None,
    ) -> None:
        try:
            await channel.delete(reason=reason)
        except discord.NotFound:
            logger.warning(f"Channel {channel.id} no longer exists")
        except discord.Forbidden as e:
            raise Exception(i18n.get_default("commands.channel.no_permission_delete")) from e

    async def rename_channel(
        self,
        channel: discord.TextChannel | discord.VoiceChannel | discord.CategoryChannel,
        new_name: str,
        reason: str | None = None,
    ) -> None:
        try:
            await channel.edit(name=new_name, reason=reason)
        except discord.Forbidden as e:
            raise Exception(i18n.get_default("commands.channel.no_permission_edit")) from e

    async def get_history(
        self,
        channel: discord.TextChannel,
        limit: int = 100,
        before: datetime.datetime | None = None,
        after: datetime.datetime | None = None,
    ) -> list[discord.Message]:
        """Fetch channel messages.

        Returns:
            List of discord.Message objects.
        """
        try:
            return [m async for m in channel.history(limit=limit, after=after, before=before)]
        except discord.Forbidden as e:
            raise Exception(i18n.get_default("commands.channel.no_permission_read")) from e
