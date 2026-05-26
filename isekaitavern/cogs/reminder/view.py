import datetime
import typing

import discord

from ...errno import PastTimeError
from ...utils.logging import logger
from .services import ReminderService


class ReminderCreateModal(discord.ui.Modal, title="📜 建立提醒事項!"):
    remind_date = discord.ui.TextInput(
        label="日期 (年-月-日)",
        placeholder="格式: YYYY-MM-DD",
        default=datetime.datetime.now().strftime("%Y-%m-%d"),
        min_length=10,
        max_length=10,
    )
    remind_time = discord.ui.TextInput(
        label="時間 (小時:分鐘)", placeholder="格式: HH:MM (24小時制)", min_length=5, max_length=5
    )
    remind_message = discord.ui.TextInput(
        label="提醒內容", placeholder="例如:該去打討伐戰了!", min_length=1, max_length=100
    )

    def __init__(self, service: ReminderService, is_user_reminder: bool):
        super().__init__()
        self.service = service
        self.is_user_reminder = is_user_reminder

    @typing.override
    async def on_submit(self, interaction: discord.Interaction):
        try:
            date_str = self.remind_date.value
            time_str = self.remind_time.value

            local_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            # TODO: 取得用戶的時區
            offset = 8

            utc_dt = local_dt - datetime.timedelta(hours=offset)
            utc_dt = utc_dt.replace(tzinfo=datetime.UTC)

            if self.is_user_reminder:
                await self.service.add_user_reminder(
                    user_id=interaction.user.id,
                    remind_time=utc_dt,
                    message=self.remind_message.value,
                )
            else:
                if not interaction.channel_id:
                    raise ValueError("channel is required")
                if not interaction.guild_id:
                    raise ValueError("channel is required")
                await self.service.add_guild_reminder(
                    user_id=interaction.user.id,
                    remind_time=utc_dt,
                    message=self.remind_message.value,
                    channel_id=interaction.channel_id,
                    guild_id=interaction.guild_id,
                )

            ts = int(utc_dt.timestamp())
            await interaction.response.send_message(
                f"✅ **傳音預約成功喵!**\n"
                f"內容:\n\n{self.remind_message.value}\n\n"
                f"時間:<t:{ts}:F> \n\n"
                f"💡 *如果時間不對,請記得用 `/timezone` 調整時區哦!*",
                ephemeral=True,
            )
        except ValueError as e:
            logger.error(e)
            await interaction.response.send_message(
                "❌ 格式好像寫錯了!請檢查日期 (YYYY-MM-DD) 與時間 (HH:MM) 格式。", ephemeral=True
            )
        except PastTimeError as e:
            logger.error(e)
            await interaction.response.send_message("❌ 預約時間已過了!", ephemeral=True)
