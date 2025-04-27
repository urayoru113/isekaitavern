import datetime
import typing

import beanie
import pydantic
import pymongo


class AnonymousSettingsModel(beanie.Document):
    guild_id: typing.Annotated[int, beanie.Indexed(unique=True)]

    enabled: bool = False
    channel_ids: set[int] = pydantic.Field(
        default_factory=set,
        description="Set of avaliable channels to send anonymous messages",
    )

    last_update_time: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self) -> None:
        self.last_update_time = datetime.datetime.now()

    class Settings:
        name = "anonymous_settings"
        use_cache = True
        cache_expiration_time = datetime.timedelta(minutes=5)


class AnonymousMemberModel(beanie.Document):
    guild_id: int
    member_id: int
    nickname: str

    avatar_url: str | None = None

    last_update_time: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self) -> None:
        self.last_update_time = datetime.datetime.now()

    class Settings:
        name = "anonymous_member"
        use_cache = True
        cache_expiration_time = datetime.timedelta(minutes=5)

        indexes: typing.ClassVar = [
            pymongo.IndexModel(
                [
                    ("guild_id", pymongo.ASCENDING),
                    ("member_id", pymongo.ASCENDING),
                ],
                unique=True,
            ),
        ]

    @classmethod
    async def find_by_indexed(cls, guild_id: int, member_id: int) -> typing.Self | None:
        return await cls.find_one(cls.guild_id == guild_id, cls.member_id == member_id)
