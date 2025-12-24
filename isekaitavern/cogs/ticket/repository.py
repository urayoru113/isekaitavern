import beanie.odm.operators.update.general as ops

from ...utils.helpers import ensure_awaitable
from .model import TicketConfig, TicketConstants, TicketRecord


class TicketRepository:
    """Handles data persistence for ticket configurations."""

    async def upsert_config(self, guild_id: int, category_id: int, admin_role_id: int | None) -> None:
        await ensure_awaitable(
            TicketConfig.find_one(TicketConfig.guild_id == guild_id).upsert(
                ops.Set({"category_id": category_id, "admin_role_id": admin_role_id}),
                on_insert=TicketConfig(guild_id=guild_id, category_id=category_id, admin_role_id=admin_role_id),
            )
        )

    async def get_config(self, guild_id: int) -> TicketConfig | None:
        return await TicketConfig.find_one(TicketConfig.guild_id == guild_id)

    async def create_record(self, guild_id: int, user_id: int, channel_id: int):
        record = TicketRecord(guild_id=guild_id, user_id=user_id, channel_id=channel_id)
        await record.insert()
        return record

    async def close_record(self, guild_id: int, channel_id: int):
        await ensure_awaitable(
            TicketRecord.find_one(TicketRecord.guild_id == guild_id, TicketRecord.channel_id == channel_id).update(
                ops.Set({"status": TicketConstants.STATUS_CLOSED})
            )
        )

    async def has_active_ticket(self, guild_id: int, user_id: int) -> bool:
        # Check if user already has an open ticket in this guild
        return (
            await TicketRecord.find_one(
                TicketRecord.guild_id == guild_id, TicketRecord.user_id == user_id, TicketRecord.status == "open"
            )
            is not None
        )
