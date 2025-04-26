import datetime
import typing

import beanie
import pydantic


class _BasicModel(beanie.Document):
    guild_id: typing.Annotated[int, beanie.Indexed(unique=True)]
    set_by_member_id: int = 0
    channel_id: int = 0
    title: str = ""
    description: str
    color: int = 0xE74C3C
    thumbnail_url: str = ""
    image_url: str = ""
    enabled: bool = True

    last_update_time: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self) -> None:
        self.last_update_time = datetime.datetime.now()


class WelcomeModel(_BasicModel):
    description: str = "Welcome {member} joined the server"

    class Settings:
        name = "welcome"


class FarewellModel(_BasicModel):
    description: str = "Farewell {member} left the server"

    class Settings:
        name = "farewell"


TVModel = typing.TypeVar("TVModel", WelcomeModel, FarewellModel)
