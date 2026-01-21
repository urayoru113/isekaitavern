import typing

import discord
from discord import app_commands
from discord.ext import commands

from isekaitavern.cogs.ticket.repository import TicketRepository

from ...bot import DiscordBot
from ...utils.logging import logger
from .model import TicketConfig, TicketRecord
from .services import TicketService
from .views import TicketCloseView, TicketLaunchView


class TicketCog(commands.Cog):
    """Manages Discord interactions and command interfaces for tickets."""

    def __init__(self, bot: DiscordBot):
        logger.info("Initializing TicketCog")
        self.bot = bot
        self.repo = TicketRepository()
        self.service = TicketService(self.repo)

    ticket = app_commands.Group(name="ticket", description="Ticket System")

    @ticket.command(name="setup")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_setup(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        admin_role: discord.Role | None = None,
    ):
        assert interaction.guild is not None
        assert isinstance(interaction.channel, discord.TextChannel)

        await interaction.response.defer(ephemeral=True)

        try:
            target_category = await self.service.set_category(
                guild=interaction.guild, category=category, admin_role_id=admin_role.id if admin_role else None
            )
            embed = discord.Embed(
                title="Support Ticket",
                description="Click the button below to open a support ticket.",
                color=discord.Color.blue(),
            )
            await interaction.channel.send(embed=embed, view=self.launch_view)
            await interaction.followup.send(f"✅ Setup complete in {target_category.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e!s}", ephemeral=True)

    @typing.override
    async def cog_load(self):
        await self.bot.init_beanie(self.bot.motor_client.db, TicketConfig, TicketRecord)

        self.launch_view = TicketLaunchView(self.service)
        self.close_view = TicketCloseView(self.service)

        self.bot.add_view(self.launch_view)
        self.bot.add_view(self.close_view)

    @typing.override
    async def cog_unload(self):
        self.launch_view.stop()
        self.close_view.stop()


async def setup(bot: DiscordBot):
    cog = TicketCog(bot)
    await bot.add_cog(cog)
