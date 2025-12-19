import typing

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
    channel_ids: set[int] = pydantic.Field(default_factory=set)
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
