import datetime
import typing

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ...bot import DiscordBot
from ...i18n import i18n
from ...utils.logging import logger
from .model import ReminderGuildRecord, ReminderUserRecord
from .repository import ReminderRepository
from .services import ReminderService
from .view import ReminderCreateModal


class ReminderCog(commands.Cog):
    def __init__(self, bot: DiscordBot):
        logger.info("Initializing ReminderCog")
        self.bot = bot
        self.repo = ReminderRepository()
        self.service = ReminderService(self.repo, self.bot)

    @typing.override
    async def cog_load(self):
        await self.bot.init_beanie(self.bot.motor_client.GuildSettings, ReminderGuildRecord, ReminderUserRecord)
        if not self.reminder_loop.is_running():
            self.reminder_loop.start()

    @typing.override
    async def cog_unload(self):
        await self.bot.init_beanie(self.bot.motor_client.GuildSettings, ReminderGuildRecord, ReminderUserRecord)
        if self.reminder_loop.is_running():
            self.reminder_loop.stop()

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        await self.service.process_due_reminders()

    reminder_group = app_commands.Group(name="reminder", description="提醒與定時推播系統")

    @reminder_group.command(name="set", description="設定提醒或伺服器定時發送")
    async def set_reminder(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.send_modal(ReminderCreateModal(self.service, interaction.guild_id is None))

    @reminder_group.command(name="list", description="列出你目前設定的所有提醒")
    async def list_reminders(self, interaction: discord.Interaction):
        reminders = await self.repo.get_due_reminders(datetime.datetime.now())
        if reminders:
            response_message = "\n".join(f"{r.title} ({r.remind_time.strftime('%m/%d %H:%M')})" for r in reminders)
        elif interaction.guild_id:
            response_message = i18n.get("zh-tw", "commands.reminder.channel_list_empty")
        else:
            response_message = i18n.get("zh-tw", "commands.reminder.user_list_empty")
        await interaction.response.send_message(response_message, ephemeral=True)

    @reminder_group.command(name="delete", description="刪除特定的提醒")
    @app_commands.describe(reminder_id="請選擇要刪除的提醒")
    async def delete_reminder(
        self,
        interaction: discord.Interaction,
        reminder_id: str,  # 建議用 ID 刪除最精準
    ):
        # 配合 Autocomplete 讓用戶用選的
        pass

    @delete_reminder.autocomplete("reminder_id")
    async def reminder_id_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """讓用戶在輸入刪除指令時,自動跳出他擁有的提醒清單"""
        reminders = await self.repo.get_user_reminders(interaction.user.id)
        return [
            app_commands.Choice(name=f"{r.title} ({r.remind_time.strftime('%m/%d %H:%M')})", value=str(r.id))
            for r in reminders
            if current.lower() in r.title.lower()
        ][:25]  # Discord 限制最多顯示 25 個


async def setup(bot: DiscordBot):
    cog = ReminderCog(bot)
    await bot.add_cog(cog)
