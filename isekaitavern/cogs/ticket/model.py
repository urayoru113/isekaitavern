import datetime

import beanie
import pydantic


class TicketConstants:
    ID_LAUNCH_VIEW = "isekai:ticket:launch_view"
    ID_CLOSE_VIEW = "isekai:ticket:close_view"

    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_ARCHIVED = "archived"


class TicketConfig(beanie.Document):
    """Configuration for the ticket system per guild."""

    guild_id: int
    category_id: int
    admin_role_id: int | None = None

    class Settings:
        name = "ticket_configs"


class TicketRecord(beanie.Document):
    """Record of an individual support ticket."""

    guild_id: int
    user_id: int
    channel_id: int
    status: str = TicketConstants.STATUS_OPEN
    created_at: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)

    class Settings:
        name = "ticket_records"
