import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot

from ...utils.logging import logger
from .model import FarewellModel, WelcomeModel
from .repository import WelcomeFarewellRepository
from .service import WelcomeFarewellService


class WelcomeFarewellCog(commands.Cog, name="guild_settings"):
    def __init__(self, bot: DiscordBot):
        logger.info("Initializing WelcomeFarewellCog")
        self.bot = bot
        self.bot._register_beanie_model(self.bot.motor_client.GuildSettings, WelcomeModel, FarewellModel)
        self.repo = WelcomeFarewellRepository()
        self.service = WelcomeFarewellService()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        model = await self.repo.get_model(WelcomeModel, member.guild.id)
        if not model:
            return

        if model.enabled and model.channel_id != 0:
            channel = member.guild.get_channel(model.channel_id)
            assert isinstance(channel, discord.TextChannel)
            if channel:
                embed = self.service.build_embed(model, member)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member) -> None:
        model = await self.repo.get_model(FarewellModel, member.guild.id)
        if not model:
            return

        if model.enabled and model.channel_id != 0:
            channel = member.guild.get_channel(model.channel_id)
            assert isinstance(channel, discord.TextChannel)
            if channel:
                embed = self.service.build_embed(model, member)
                await channel.send(embed=embed)

    @commands.hybrid_group()
    @commands.guild_only()
    async def welcome(self, _: commands.Context): ...

    @commands.hybrid_group()
    @commands.guild_only()
    async def farewell(self, _: commands.Context): ...

    @welcome.command(name="enable")
    @commands.guild_only()
    async def welcome_enable(self, ctx: commands.Context):
        """允許歡迎訊息"""
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, enabled=True)

    @farewell.command("enable")
    async def farewell_enable(self, ctx: commands.Context):
        """允許離開訊息"""
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, enabled=True)

    @welcome.command(name="disable")
    @commands.guild_only()
    async def welcome_disable(self, ctx: commands.Context):
        """禁止歡迎訊息"""
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, enabled=False)

    @farewell.command(name="disable")
    async def farewell_disable(self, ctx: commands.Context):
        """禁止離開訊息"""
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, enabled=False)

    @welcome.command(name="message")
    async def welcome_message(self, ctx: commands.Context, *, message: str):
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, description=message)

    @farewell.command(name="message")
    async def farewell_message(self, ctx: commands.Context, *, message: str):
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, description=message)

    @welcome.command(name="channel")
    async def welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, channel_id=channel.id)

    @farewell.command(name="channel")
    async def farewell_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, channel_id=channel.id)

    @welcome.command(name="title")
    async def welcome_title(self, ctx: commands.Context, title: str):
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, title=title)

    @farewell.command(name="title")
    async def farewell_title(self, ctx: commands.Context, title: str):
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, title=title)

    @welcome.command(name="color")
    async def welcome_color(self, ctx: commands.Context, color: discord.Color) -> None:
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, color=color.value)

    @farewell.command(name="color")
    async def farewell_color(self, ctx: commands.Context, color: discord.Color) -> None:
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, color=color.value)

    @welcome.command(name="thumbnail")
    async def welcome_thumbnail(self, ctx: commands.Context, url: str = "") -> None:
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, thumbnail_url=url)

    @farewell.command(name="thumbnail")
    async def farewell_thumbnail(self, ctx: commands.Context, url: str = "") -> None:
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, thumbnail_url=url)

    @welcome.command(name="image")
    async def welcome_image(self, ctx: commands.Context, url: str = "") -> None:
        assert ctx.guild is not None
        await self.repo.set_model(WelcomeModel, ctx.guild.id, image_url=url)

    @farewell.command(name="image")
    async def farewell_image(self, ctx: commands.Context, url: str = "") -> None:
        assert ctx.guild is not None
        await self.repo.set_model(FarewellModel, ctx.guild.id, image_url=url)

    @welcome.command(name="demo")
    async def welcome_demo(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None
        assert isinstance(ctx.author, discord.Member)
        model = await self.repo.get_model(WelcomeModel, ctx.guild.id)
        if model:
            embed = self.service.build_embed(model, ctx.author)
            await ctx.channel.send(embed=embed)

    @farewell.command(name="demo")
    async def farewell_demo(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None
        assert isinstance(ctx.author, discord.Member)
        model = await self.repo.get_model(FarewellModel, ctx.guild.id)
        if model:
            embed = self.service.build_embed(model, ctx.author)
            await ctx.channel.send(embed=embed)


async def setup(bot: DiscordBot):
    """Add greeting cog."""
    await bot.add_cog(WelcomeFarewellCog(bot))
