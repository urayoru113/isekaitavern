import datetime
import typing

import beanie
import pydantic
from pymongo import ASCENDING, IndexModel

from .schemes import WelcomeFarewellEmbed


class _WelcomeFarewellBasic(pydantic.BaseModel):
    guild_id: int
    channel_id: int = 0
    title: str = ""
    description: str
    color: int = 0xE67E22  # discord.Color.orange
    thumbnail_url: str = ""
    image_url: str = ""
    enabled: bool = False

    last_update_time: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self) -> None:
        self.last_update_time = datetime.datetime.now()

    def to_embed_dict(self) -> WelcomeFarewellEmbed:
        return {
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "thumbnail": self.thumbnail_url,
            "image": self.image_url,
        }


class _WelcomeFarewellSettings:
    name: str
    indexes: typing.ClassVar[list[IndexModel]] = [
        IndexModel(
            [("guild_id", ASCENDING)],
            unique=True,
        ),
    ]


class WelcomeModel(_WelcomeFarewellBasic, beanie.Document):
    description: str = "Welcome {member} joined the server"

    class Settings(_WelcomeFarewellSettings):
        name = "welcome"


class FarewellModel(_WelcomeFarewellBasic, beanie.Document):
    description: str = "Farewell {member} left the server"

    class Settings(_WelcomeFarewellSettings):
        name = "farewell"


WelcomeFarewellModelT = typing.TypeVar("WelcomeFarewellModelT", WelcomeModel, FarewellModel)
