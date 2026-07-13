import io

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from ...bot import DiscordBot
from ...i18n import i18n
from ...services.channel import ChannelService
from ...utils.logging import logger
from ...utils.messages import extract_message


class AICog(commands.Cog):
    """AI-powered commands."""

    _MAX_EMBED_LENGTH = 1900

    def __init__(self, bot: DiscordBot):
        logger.info("Initializing AICog")
        self.bot = bot
        self.channel_service = ChannelService()

    @app_commands.command(name="summary", description="生成頻道訊息摘要")
    async def summarize(self, interaction: discord.Interaction, limit: int = 10):
        if not isinstance(interaction.channel, discord.TextChannel):
            embed = discord.Embed(
                description=i18n.get_default("commands.ai.invalid_channel"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer()
        try:
            messages = await self.channel_service.get_history(interaction.channel, limit)
            if not messages:
                embed = discord.Embed(
                    description=i18n.get_default("commands.ai.no_messages"),
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return

            data = [extract_message(m) for m in messages]
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "http://127.0.0.1:8000/summary",  # TODO: change to env
                    json=data,
                )
                response.raise_for_status()

            output = response.text
            if len(output) > self._MAX_EMBED_LENGTH:
                # HACK: use better way handling large output(considering streaming or resend to endpoint)
                file = discord.File(
                    fp=io.BytesIO(output.encode("utf-8")),
                    filename="summary.json",
                )
                await interaction.followup.send(file=file)
            else:
                await interaction.followup.send(f"```json\n{output}\n```")
        except Exception as e:
            # XXX :add logging
            embed = discord.Embed(
                description=str(e),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: DiscordBot):
    cog = AICog(bot)
    await bot.add_cog(cog)
