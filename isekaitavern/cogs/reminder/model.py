import datetime
import enum
import typing

import beanie
import pydantic
import pymongo


class ReminderRecurrence(enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class ReminderUserRecord(beanie.Document):
    user_id: int
    message: str
    remind_time: datetime.datetime
    recurrence: ReminderRecurrence = ReminderRecurrence.ONCE
    created_at: datetime.datetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    @property
    def is_user_reminder(self) -> bool:
        return True

    class Settings:
        name = "user_reminder_records"
        indexes = (
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING)],
            ),
        )


class ReminderGuildRecord(beanie.Document):
    user_id: int
    channel_id: int
    guild_id: int
    message: str
    remind_time: datetime.datetime
    recurrence: ReminderRecurrence = ReminderRecurrence.ONCE
    created_at: datetime.datetime = pydantic.Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    @property
    def is_user_reminder(self) -> bool:
        return False

    class Settings:
        name = "guild_reminder_records"
        indexes = (
            pymongo.IndexModel(
                [("channel_id", pymongo.ASCENDING)],
            ),
        )


ReminderRecordT = typing.TypeVar("ReminderRecordT", ReminderGuildRecord, ReminderUserRecord)
ReminderRecordU = ReminderGuildRecord | ReminderUserRecord
