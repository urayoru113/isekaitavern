import discord

from ...utils.logging import logger
from .repository import TicketRepository


class TicketService:
    """Orchestrates business logic for the ticket system."""

    def __init__(self, repo: TicketRepository) -> None:
        self.repo = repo

    async def set_category(
        self, guild: discord.Guild, category: discord.CategoryChannel, admin_role_id: int | None
    ) -> discord.CategoryChannel:
        await self.repo.upsert_config(guild_id=guild.id, category_id=category.id, admin_role_id=admin_role_id)
        return category

    async def open_ticket(self, guild: discord.Guild, user: discord.Member) -> discord.TextChannel:
        config = await self.repo.get_config(guild.id)
        if not config:
            raise Exception("Ticket system is not set up. Please run /ticket setup first.")

        if await self.repo.has_active_ticket(guild.id, user.id):
            raise Exception("You already have an active ticket.")

        category = guild.get_channel(config.category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            raise Exception("Target category not found. Please re-run setup.")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if config.admin_role_id:
            admin_role = guild.get_role(config.admin_role_id)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel_name = f"ticket-{user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket for {user.display_name} (ID: {user.id})",
        )

        await self.repo.create_record(guild.id, user.id, ticket_channel.id)
        return ticket_channel

    async def close_ticket(self, guild: discord.Guild, channel: discord.TextChannel, user: discord.Member) -> None:
        await self.repo.close_record(guild.id, channel.id)
        try:
            await channel.delete(reason=f"Ticket closed by {user.name}")
        except discord.NotFound:
            logger.warning(f"Channel {channel.id} already deleted.")
        except discord.Forbidden as e:
            raise Exception("Bot lacks permission to delete this channel.") from e
