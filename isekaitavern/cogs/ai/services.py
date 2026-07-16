import datetime

import discord

from ...i18n import i18n


class ChannelService:
    """Business logic for channel management: create, delete, rename."""

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
