import datetime
import typing

import beanie
import pydantic


class WelcomeModel(beanie.Document):
    guild_id: int = pydantic.Field(..., index=True)  # pyright: ignore[reportCallIssue]
    channel_id: int = 0
    title: str = ""
    description: str = ""
    color: int = 0xE74C3C
    thumbnail_url: str = ""
    image_url: str = ""
    set_by_member_id: int = 0
    last_update_time: str = pydantic.Field(default_factory=lambda: datetime.datetime.now().isoformat())
    enabled: bool = True

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self):
        self.last_update_time = datetime.datetime.now().isoformat()

    class Settings:
        name = "welcome"


class FarewellModel(beanie.Document):
    guild_id: int = pydantic.Field(..., index=True)  # pyright: ignore[reportCallIssue]
    channel_id: int = 0
    title: str = ""
    description: str = ""
    color: int = 0xE74C3C
    thumbnail_url: str = ""
    image_url: str = ""
    set_by_member_id: int = 0
    last_update_time: str = pydantic.Field(default_factory=lambda: datetime.datetime.now().isoformat())

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self):
        self.last_update_time = datetime.datetime.now().isoformat()

    class Settings:
        name = "farewell"


TVModel = typing.TypeVar("TVModel", WelcomeModel, FarewellModel)
