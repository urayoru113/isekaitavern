import datetime

import beanie
import pydantic


class WelcomeFareWellModel(beanie.Document):
    guild_id: int = pydantic.Field(..., index=True)  # pyright: ignore[reportCallIssue]
    welcome_message: str = ""
    farewell_message: str = ""
    set_by_member_id: int
    last_update_time: str = pydantic.Field(default_factory=lambda: datetime.datetime.now().isoformat())

    @beanie.before_event(beanie.Save)
    def update_last_update_time(self):
        self.last_update_time = datetime.datetime.now().isoformat()

    class Settings:
        name = "greeting"
