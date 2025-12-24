import discord

from .model import TicketConstants
from .services import TicketService


class TicketLaunchView(discord.ui.View):
    def __init__(self, service: TicketService):
        super().__init__(timeout=None)
        self.service = service

    @discord.ui.button(
        label="Create Ticket", style=discord.ButtonStyle.primary, emoji="📩", custom_id=TicketConstants.ID_LAUNCH_VIEW
    )
    async def create_ticket(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)

        try:
            channel = await self.service.open_ticket(interaction.guild, interaction.user)
            await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)
            view = TicketCloseView(self.service)
            await channel.send(f"Welcome {interaction.user.mention}, support will be with you shortly.", view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ {e!s}", ephemeral=True)


class TicketCloseView(discord.ui.View):
    def __init__(self, service: TicketService):
        super().__init__(timeout=None)
        self.service = service

    @discord.ui.button(
        label="Close Ticket", style=discord.ButtonStyle.primary, emoji="❌", custom_id=TicketConstants.ID_CLOSE_VIEW
    )
    async def create_ticket(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer()
        assert interaction.guild is not None
        assert isinstance(interaction.channel, discord.TextChannel)
        assert isinstance(interaction.user, discord.Member)

        try:
            await self.service.close_ticket(interaction.guild, interaction.channel, interaction.user)
        except Exception as e:
            await interaction.followup.send(f"❌ {e!s}", ephemeral=True)
