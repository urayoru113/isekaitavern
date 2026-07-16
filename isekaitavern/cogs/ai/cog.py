import io
import urllib.parse

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from ...bot import DiscordBot
from ...config import app_config
from ...i18n import i18n
from ...utils.logging import logger
from ...utils.messages import extract_message
from .services import ChannelService


class AICog(commands.Cog):
    """AI-powered commands."""

    _MAX_EMBED_LENGTH = 1900

    def __init__(self, bot: DiscordBot):
        logger.info("Initializing AICog")
        self.bot = bot
        self.channel_service = ChannelService()

    @app_commands.command(name="summarize", description="生成頻道訊息摘要")
    @app_commands.describe(limit="摘要的消息數量")
    async def summarize(self, interaction: discord.Interaction, limit: int = 100):
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
                    urllib.parse.urljoin(app_config.assistance_url, "summary"),  # OPTIM: do modularize
                    json=data,
                )
                response.raise_for_status()

            output = response.json()["data"]["summary"]  # XXX: handle key not found
            if len(output) > self._MAX_EMBED_LENGTH:
                # HACK: use better way handling large output(considering streaming or resend to endpoint)
                file = discord.File(
                    fp=io.BytesIO(output.encode("utf-8")),
                    filename="summary.json",
                )
                await interaction.followup.send(file=file)
            else:
                await interaction.followup.send(output)
        except Exception as e:
            # XXX: add logging
            embed = discord.Embed(
                description=str(e),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="ask", description="詢問AI問題")
    @app_commands.describe(query="要問的問題")
    async def query(self, interaction: discord.Interaction, query: str):
        if not isinstance(interaction.channel, discord.TextChannel):
            embed = discord.Embed(
                description=i18n.get_default("commands.ai.invalid_channel"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer()

        try:
            data = {"content": query}  # OPTIM:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    urllib.parse.urljoin(app_config.assistance_url, "ask"),  # OPTIM: do modularize
                    json=data,
                )
                response.raise_for_status()
            output = response.json()["data"]["content"]  # XXX: handle key not found
            await interaction.followup.send(output)
        except Exception as e:
            embed = discord.Embed(
                description=str(e),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: DiscordBot):
    cog = AICog(bot)
    await bot.add_cog(cog)
