import typing
from datetime import datetime

import beanie
import pydantic
import pymongo


class AnonymousBaseSettings(beanie.Document):
    """
    Guild-level anonymous feature configuration

    Fields:
        guild_id: Discord guild ID
        enabled: Whether anonymous feature is enabled
        channel_ids: List of channel IDs where anonymous messages can be sent
        cooldown_seconds: Cooldown time between anonymous messages
        blocked_users: List of user IDs blocked from using anonymous feature
    """

    guild_id: int
    enabled: bool = False
    cooldown_seconds: int = 10
    blocked_users: set[int] = pydantic.Field(default_factory=set)

    class Settings:
        name = "anonymous_config"
        indexes: typing.ClassVar[list[pymongo.IndexModel]] = [
            pymongo.IndexModel(
                [("guild_id", pymongo.ASCENDING)],
                unique=True,
                name="unique_guild_id",
            )
        ]


class AnonymousWebhookInfo(beanie.Document):
    """
    Durable storage for anonymous webhooks per channel
    """

    guild_id: int
    channel_id: int
    webhook_id: int
    webhook_token: str
    updated_at: datetime | None = None

    class Settings:
        name = "anonymous_webhook_auth"
        indexes: typing.ClassVar[list[pymongo.IndexModel]] = [
            pymongo.IndexModel(
                [("channel_id", pymongo.ASCENDING)],
                unique=True,
                name="unique_channel_id",
            )
        ]


class AnonymousUserSettings(beanie.Document):
    """
    User-specific anonymous settings for each guild

    Fields:
        guild_id: Discord guild ID
        user_id: Discord user ID
        display_name: Anonymous display name
        avatar_url: Anonymous avatar URL
    """

    guild_id: int
    user_id: int
    display_name: str = "anonymous"
    avatar_url: str = ""

    class Settings:
        name = "anonymous_user_settings"
        indexes: typing.ClassVar[list[pymongo.IndexModel]] = [
            pymongo.IndexModel(
                [("guild_id", pymongo.ASCENDING), ("user_id", pymongo.ASCENDING)],
                unique=True,
                name="unique_guild_user",
            )
        ]
