import asyncio
import datetime

from beanie import PydanticObjectId

from .model import ReminderGuildRecord, ReminderRecordU, ReminderRecurrence, ReminderUserRecord


class ReminderRepository:
    async def create_user_reminder(
        self,
        user_id: int,
        message: str,
        remind_time: datetime.datetime,
        recurrence: ReminderRecurrence = ReminderRecurrence.ONCE,
    ) -> ReminderUserRecord:
        record = ReminderUserRecord(
            user_id=user_id,
            message=message,
            remind_time=remind_time,
            recurrence=recurrence,
        )
        return await record.insert()

    async def create_guild_reminder(
        self,
        user_id: int,
        message: str,
        remind_time: datetime.datetime,
        channel_id: int,
        guild_id: int,
        recurrence: ReminderRecurrence = ReminderRecurrence.ONCE,
    ) -> ReminderGuildRecord:
        record = ReminderGuildRecord(
            user_id=user_id,
            message=message,
            remind_time=remind_time,
            channel_id=channel_id,
            guild_id=guild_id,
            recurrence=recurrence,
        )
        return await record.insert()

    async def get_due_reminders(self, now: datetime.datetime) -> list[ReminderRecordU]:
        results = await asyncio.gather(
            ReminderUserRecord.find(ReminderUserRecord.remind_time <= now).to_list(),
            ReminderGuildRecord.find(ReminderGuildRecord.remind_time <= now).to_list(),
        )

        return sorted([x for sublist in results for x in sublist], key=lambda r: r.remind_time)

    async def get_user_reminders(self, user_id: int) -> list[ReminderUserRecord]:
        return await ReminderUserRecord.find(ReminderUserRecord.user_id == user_id).sort("+remind_time").to_list()

    async def get_guild_reminders(self, guild_id: int) -> list[ReminderGuildRecord]:
        return await ReminderGuildRecord.find(ReminderGuildRecord.guild_id == guild_id).sort("+remind_time").to_list()

    async def get_reminder_by_id(self, reminder_id: str) -> ReminderRecordU | None:
        try:
            document_id = PydanticObjectId(reminder_id)
            return await ReminderUserRecord.get(document_id) or await ReminderGuildRecord.get(document_id)
        except Exception:
            return None

    async def delete_reminder(self, reminder_id: str) -> bool:
        reminder = await self.get_reminder_by_id(reminder_id)
        if reminder:
            await reminder.delete()
            return True
        return False
