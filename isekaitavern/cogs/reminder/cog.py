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
        if self.reminder_loop.is_running():
            self.reminder_loop.stop()

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        await self.service.process_due_reminders()

    reminder_group = app_commands.Group(name="reminder", description="提醒與定時推播系統")

    @app_commands.default_permissions(administrator=True)
    @reminder_group.command(name="set", description="設定提醒或伺服器定時發送")
    async def set_reminder(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild_id:
            if interaction.channel is None or not isinstance(interaction.user, discord.Member):
                embed = discord.Embed(
                    description=i18n.get("zh-tw", "commands.reminder.invalid_state"),
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            permissions = interaction.channel.permissions_for(interaction.user)
            if not permissions.manage_guild:
                embed = discord.Embed(
                    description=i18n.get("zh-tw", "commands.reminder.no_permission"),
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        await interaction.response.send_modal(ReminderCreateModal(self.service, interaction.guild_id is None))

    @reminder_group.command(name="list", description="列出你目前設定的所有提醒")
    async def list_reminders(self, interaction: discord.Interaction):
        if interaction.guild_id:
            reminders = await self.repo.get_channel_reminders(interaction.channel_id) if interaction.channel_id else []
            title = i18n.get("zh-tw", "commands.reminder.channel_list_title")
        else:
            reminders = await self.repo.get_user_reminders(interaction.user.id)
            title = i18n.get("zh-tw", "commands.reminder.user_list_title")

        embed = discord.Embed(title=title, color=discord.Color.blue())
        if reminders:
            for r in reminders:
                embed.add_field(
                    name=f"⏰ {r.remind_time.strftime('%m/%d %H:%M')}",
                    value=r.message,
                    inline=False,
                )
        elif interaction.guild_id:
            embed.description = i18n.get("zh-tw", "commands.reminder.channel_list_empty")
        else:
            embed.description = i18n.get("zh-tw", "commands.reminder.user_list_empty")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.default_permissions(administrator=True)
    @reminder_group.command(name="delete", description="刪除特定的提醒")
    @app_commands.describe(reminder_id="請選擇要刪除的提醒")
    async def delete_reminder(
        self,
        interaction: discord.Interaction,
        reminder_id: str,
    ):
        if interaction.guild_id:
            if interaction.channel is None or not isinstance(interaction.user, discord.Member):
                embed = discord.Embed(
                    description=i18n.get("zh-tw", "commands.reminder.invalid_state"),
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            permissions = interaction.channel.permissions_for(interaction.user)
            if not permissions.manage_guild:
                embed = discord.Embed(
                    description=i18n.get("zh-tw", "commands.reminder.no_permission"),
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        reminder = await self.repo.get_reminder_by_id(reminder_id)
        if not reminder:
            embed = discord.Embed(
                description=i18n.get("zh-tw", "commands.reminder.delete_not_found"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await reminder.delete()
        embed = discord.Embed(
            description=i18n.get("zh-tw", "commands.reminder.delete_success", message=reminder.message),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @delete_reminder.autocomplete("reminder_id")
    async def reminder_id_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """讓用戶在輸入刪除指令時,自動跳出他擁有的提醒清單"""
        if interaction.guild_id:
            reminders = await self.repo.get_channel_reminders(interaction.channel_id) if interaction.channel_id else []
        else:
            reminders = await self.repo.get_user_reminders(interaction.user.id)
        return [
            app_commands.Choice(name=f"{r.message} ({r.remind_time.strftime('%m/%d %H:%M')})", value=str(r.id))
            for r in reminders
            if current.lower() in r.message.lower()
        ][:25]  # Discord 限制最多顯示 25 個


async def setup(bot: DiscordBot):
    cog = ReminderCog(bot)
    await bot.add_cog(cog)
