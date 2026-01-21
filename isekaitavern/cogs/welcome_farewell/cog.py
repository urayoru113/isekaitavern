import discord
from discord import app_commands
from discord.ext import commands

from ... import i18n
from ...bot import DiscordBot
from ...utils.logging import logger
from .model import FarewellModel, WelcomeModel
from .repository import WelcomeFarewellRepository
from .service import WelcomeFarewellService


class WelcomeFarewellCog(commands.Cog, name="guild_settings"):
    def __init__(self, bot: DiscordBot):
        logger.info("Initializing WelcomeFarewellCog")
        self.bot = bot
        self.repo = WelcomeFarewellRepository()
        self.service = WelcomeFarewellService()

    async def cog_load(self):
        await self.bot.init_beanie(self.bot.motor_client.db, WelcomeModel, FarewellModel)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        model = await self.repo.get_welcome_farewell_model(WelcomeModel, member.guild.id)
        if not model:
            return

        if model.enabled and model.channel_id != 0:
            channel = member.guild.get_channel(model.channel_id)
            if isinstance(channel, discord.TextChannel):
                embed = self.service.build_message(model, member)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member) -> None:
        model = await self.repo.get_welcome_farewell_model(FarewellModel, member.guild.id)
        if not model:
            return

        if model.enabled and model.channel_id != 0:
            channel = member.guild.get_channel(model.channel_id)
            if isinstance(channel, discord.TextChannel):
                embed = self.service.build_message(model, member)
                await channel.send(embed=embed)

    welcome = app_commands.Group(
        name="welcome",
        description="Welcome message settings",
        guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True),
    )
    farewell = app_commands.Group(
        name="farewell",
        description="Farewell message settings",
        guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="enable")
    async def welcome_enable(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, enabled=True)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.welcome.enable"))

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="enable")
    async def farewell_enable(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, enabled=True)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.farewell.enable"))

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="disable")
    async def welcome_disable(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, enabled=False)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.welcome.disable"))

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="disable")
    async def farewell_disable(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, enabled=False)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.farewell.disable"))

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="message")
    async def welcome_message(self, interaction: discord.Interaction, message: str = ""):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, description=message)
        model = await self.repo.get_welcome_farewell_model(WelcomeModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="message")
    async def farewell_message(self, interaction: discord.Interaction, message: str = ""):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, description=message)
        model = await self.repo.get_welcome_farewell_model(FarewellModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="channel")
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        assert interaction.guild is not None
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, channel_id=channel.id)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.welcome.channel", channel=channel.mention))

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="channel")
    async def farewell_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        assert interaction.guild is not None
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, channel_id=channel.id)
        await interaction.response.send_message(i18n.get("zh-tw", "commands.farewell.channel", channel=channel.mention))

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="title")
    async def welcome_title(self, interaction: discord.Interaction, title: str = ""):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, title=title)
        model = await self.repo.get_welcome_farewell_model(WelcomeModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="title")
    async def farewell_title(self, interaction: discord.Interaction, title: str = ""):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, title=title)
        model = await self.repo.get_welcome_farewell_model(FarewellModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="color")
    async def welcome_color(self, interaction: discord.Interaction, color: str) -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        color_value = self.service.get_color(color)
        if color_value:
            await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, color=color_value)
            model = await self.repo.get_welcome_farewell_model(WelcomeModel, interaction.guild.id)
            assert model is not None
            embed = self.service.build_message(model, interaction.user)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Invalid color value")

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="color")
    async def farewell_color(self, interaction: discord.Interaction, color: str) -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        color_value = self.service.get_color(color)
        if color_value:
            await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, color=color_value)
            model = await self.repo.get_welcome_farewell_model(FarewellModel, interaction.guild.id)
            assert model is not None
            embed = self.service.build_message(model, interaction.user)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Invalid color value")

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="thumbnail")
    async def welcome_thumbnail(self, interaction: discord.Interaction, url: str = "") -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, thumbnail_url=url)
        model = await self.repo.get_welcome_farewell_model(WelcomeModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="thumbnail")
    async def farewell_thumbnail(self, interaction: discord.Interaction, url: str = "") -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, thumbnail_url=url)
        model = await self.repo.get_welcome_farewell_model(FarewellModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="image")
    async def welcome_image(self, interaction: discord.Interaction, url: str = "") -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id, image_url=url)
        model = await self.repo.get_welcome_farewell_model(WelcomeModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="image")
    async def farewell_image(self, interaction: discord.Interaction, url: str = "") -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id, image_url=url)
        model = await self.repo.get_welcome_farewell_model(FarewellModel, interaction.guild.id)
        assert model is not None
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @welcome.command(name="demo")
    async def welcome_demo(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        model = await self.repo.get_welcome_farewell_model(WelcomeModel, interaction.guild.id)
        if not model:
            await self.repo.set_welcome_farewell_model(WelcomeModel, interaction.guild.id)
            model = WelcomeModel(guild_id=interaction.guild.id)
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @farewell.command(name="demo")
    async def farewell_demo(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        model = await self.repo.get_welcome_farewell_model(FarewellModel, interaction.guild.id)
        if not model:
            await self.repo.set_welcome_farewell_model(FarewellModel, interaction.guild.id)
            model = FarewellModel(guild_id=interaction.guild.id)
        embed = self.service.build_message(model, interaction.user)
        await interaction.response.send_message(embed=embed)


async def setup(bot: DiscordBot):
    await bot.add_cog(WelcomeFarewellCog(bot))
