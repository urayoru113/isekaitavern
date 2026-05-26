import asyncio
import datetime

import discord
from dateutil.relativedelta import relativedelta

from isekaitavern.bot import DiscordBot
from isekaitavern.cogs.reminder.repository import ReminderRepository

from ...errno import PastTimeError
from ...utils.logging import logger
from .model import ReminderGuildRecord, ReminderRecordU, ReminderRecurrence, ReminderUserRecord


class ReminderService:
    def __init__(self, repo: ReminderRepository, bot: DiscordBot):
        self.repo = repo
        self.bot = bot

    async def add_user_reminder(
        self,
        user_id: int,
        message: str,
        remind_time: datetime.datetime,
        recurrence: ReminderRecurrence = ReminderRecurrence.ONCE,
    ) -> ReminderUserRecord:
        if remind_time < datetime.datetime.now(datetime.UTC):
            raise PastTimeError("Remind time cannot be in the past.")
        return await self.repo.create_user_reminder(
            user_id=user_id,
            message=message,
            remind_time=remind_time,
            recurrence=recurrence,
        )

    async def add_guild_reminder(
        self,
        user_id: int,
        message: str,
        remind_time: datetime.datetime,
        channel_id: int,
        guild_id: int,
        recurrence: ReminderRecurrence = ReminderRecurrence.ONCE,
    ) -> ReminderGuildRecord:
        if remind_time < datetime.datetime.now(datetime.UTC):
            raise PastTimeError("Remind time cannot be in the past.")
        return await self.repo.create_guild_reminder(
            user_id=user_id,
            message=message,
            remind_time=remind_time,
            channel_id=channel_id,
            guild_id=guild_id,
            recurrence=recurrence,
        )

    async def process_due_reminders(self):
        now = datetime.datetime.now(datetime.UTC)
        due_reminders = await self.repo.get_due_reminders(now)

        for reminder in due_reminders:
            await self.send_reminder_message(reminder)

            if reminder.recurrence == ReminderRecurrence.ONCE:
                await reminder.delete()
            else:
                next_time = self.calculate_next_time(reminder.remind_time, reminder.recurrence)
                reminder.remind_time = next_time
                await reminder.save()

            delay = 1.2 if reminder.is_user_reminder else 0.3
            await asyncio.sleep(delay)

    async def send_reminder_message(self, reminder: ReminderRecordU) -> None:
        try:
            message_content = f"{reminder.message}"

            if reminder.is_user_reminder:
                target = self.bot.get_user(reminder.user_id)
                if not target:
                    raise ValueError("Target user not found", reminder.channel_id)
            else:
                target = self.bot.get_channel(reminder.channel_id)
                if not target:
                    raise ValueError("Target channel not found", reminder.channel_id)
                if not isinstance(target, discord.TextChannel):
                    raise ValueError("Target channel is not a text channel", reminder.channel_id)
            await target.send(message_content)
        except Exception as e:
            logger.error(f"Error sending reminder message: {e}")

    def calculate_next_time(self, current_time: datetime.datetime, recurrence: ReminderRecurrence) -> datetime.datetime:
        """計算循環提醒的下一個時間點"""
        if recurrence == ReminderRecurrence.DAILY:
            return current_time + datetime.timedelta(days=1)
        elif recurrence == ReminderRecurrence.WEEKLY:
            return current_time + datetime.timedelta(weeks=1)
        elif recurrence == ReminderRecurrence.MONTHLY:
            return current_time + relativedelta(months=1)
        elif recurrence == ReminderRecurrence.YEARLY:
            return current_time + relativedelta(years=1)
        return current_time

    def convert_to_utc(self, year, month, day, hour, minute, user_tz_offset=8) -> datetime.datetime:
        """
        將用戶輸入的時間轉為 UTC。
        MVP 階段:預設為 UTC+8 (台北時間),未來可改為動態獲取用戶時區。
        """
        # 如果沒填年月日,預設為今天
        now = datetime.datetime.now()
        dt = datetime.datetime(
            year=year or now.year, month=month or now.month, day=day or now.day, hour=hour, minute=minute
        )
        # 簡單的時區轉換:用戶時間 - 偏移量 = UTC
        return dt - datetime.timedelta(hours=user_tz_offset)
