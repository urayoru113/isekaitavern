import contextlib
import typing

import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.enums import Color
from isekaitavern.services.repository import RedisClient
from isekaitavern.utils.context_helper import fetch_guild, fetch_member

from .core import WelcomeFarewell
from .model import FarewellModel, TVModel, WelcomeModel


class WelcomeFarewellCog(commands.Cog, name="guild_settings"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.bot._register_beanie_model(self.bot.motor_client.GuildSettings, WelcomeModel, FarewellModel)
        self.guild_client = WelcomeFarewell(self.redis_client)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self._on_event(WelcomeModel, member)

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member) -> None:
        await self._on_event(FarewellModel, member)

    @commands.hybrid_group()
    async def welcome(self, _: commands.Context):...

    @commands.hybrid_group()
    async def farewell(self, _: commands.Context):...

    @welcome.command(name="message")
    async def welcome_message(self, ctx: commands.Context, channel: discord.TextChannel, title: str, *, msg: str):
        await self._set_msg(WelcomeModel, ctx, channel, title, msg)

    @farewell.command(name="message")
    async def farewell_message(self, ctx: commands.Context, channel: discord.TextChannel, title: str, *, msg: str):
        await self._set_msg(FarewellModel, ctx, channel, title, msg)

    @welcome.command(name="color")
    async def welcome_color(self, ctx: commands.Context, maybe_color: str) -> None:
        set_by_member = fetch_member(ctx)
        with contextlib.suppress(ValueError):
            maybe_color = Color.from_str(maybe_color.upper()).value

        try:
            color = discord.Color.from_str(maybe_color).value
        except ValueError:
            await ctx.send("Invalid color name or hex code")
            return

        guild = fetch_guild(ctx)
        welcome_model = await self.guild_client.require_model(WelcomeModel, guild.id)
        welcome_model.color = color
        await welcome_model.save()
        embed = self._get_embed(
            welcome_model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        await ctx.reply("Updated color successfully\nmessage:\n", embed=embed)

    @farewell.command(name="color")
    async def farewell_color(self, ctx: commands.Context, maybe_color: str) -> None:
        set_by_member = fetch_member(ctx)
        with contextlib.suppress(ValueError):
            maybe_color = Color.from_str(maybe_color.upper()).value

        try:
            color = discord.Color.from_str(maybe_color).value
        except ValueError:
            await ctx.send("Invalid color name or hex code")
            return

        guild = fetch_guild(ctx)
        farewell_model = await self.guild_client.require_model(FarewellModel, guild.id)
        farewell_model.color = color
        await farewell_model.save()
        embed = self._get_embed(
            farewell_model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        await ctx.reply("Updated color successfully\nmessage:\n", embed=embed)

    @welcome.command(name="thumbnail")
    async def welcome_thumbnail(self, ctx: commands.Context, url: str = "") -> None:
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        welcome_model = await self.guild_client.require_model(WelcomeModel, guild.id)
        welcome_model.thumbnail_url = url
        await welcome_model.save()
        embed = self._get_embed(
            welcome_model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        await ctx.reply("Updated color successfully\nmessage:\n", embed=embed)

    @farewell.command(name="thumbnail")
    async def farewell_thumbnail(self, ctx: commands.Context, url: str = "") -> None:
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        farewell_model = await self.guild_client.require_model(FarewellModel, guild.id)
        farewell_model.thumbnail_url = url
        await farewell_model.save()
        embed = self._get_embed(
            farewell_model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        await ctx.reply("Updated color successfully\nmessage:\n", embed=embed)

    @welcome.command(name="image")
    async def welcome_image(self, ctx: commands.Context, url: str = "") -> None:
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        welcome_model = await self.guild_client.require_model(WelcomeModel, guild.id)
        welcome_model.image_url = url
        await welcome_model.save()
        embed = self._get_embed(
            welcome_model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        await ctx.reply("Updated color successfully\nmessage:\n", embed=embed)

    @farewell.command(
        name="image",
        help="Sets the image for the welcome and farewell embeds. Accepts a URL.",
    )
    async def image(self, ctx: commands.Context, url: str = "") -> None:
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        farewell_model = await self.guild_client.require_model(FarewellModel, guild.id)
        farewell_model.image_url = url
        await farewell_model.save()
        embed = self._get_embed(
            farewell_model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        await ctx.reply("Updated color successfully\nmessage:\n", embed=embed)

    async def _on_event(self, model_cls: type[TVModel], member: discord.Member) -> None:
        model = await self.guild_client.get_model(model_cls, member.guild.id)

        if not model or not model.enabled:
            return

        embed = self._get_embed(
            model,
            member=f"<@{member.id}>",
            member_icon=member.display_avatar.url,
            member_banner=member.display_banner.url if member.display_banner else "",
        )

        channel = discord.utils.get(member.guild.channels, id=model.channel_id)

        if not channel or not isinstance(channel, discord.TextChannel):
            return

        await channel.send(embed=embed)

    async def _set_msg(
        self,
        model_cls: type[TVModel],
        ctx: commands.Context,
        channel: discord.TextChannel,
        title: str,
        msg: str,
    ):
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        await self.guild_client.set_model(model_cls, guild.id, set_by_member.id, channel.id, title, msg)

        model = await self.guild_client.require_model(model_cls, guild.id)

        embed = self._get_embed(
            model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )

        await ctx.reply(f"Updated {model_cls.__name__} message successfully\nmessage:\n", embed=embed)

    def _get_embed(self, model: TVModel, **format_kwargs: str) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color(model.color),
            title=model.title.format(**format_kwargs),
            description=model.description.format(**format_kwargs),
        )
        if model.thumbnail_url:
            embed.set_thumbnail(url=model.thumbnail_url.format(**format_kwargs))
        if model.image_url:
            embed.set_image(url=model.image_url.format(**format_kwargs))
        return embed

    @property
    def redis_client(self) -> RedisClient:
        assert self.bot.redis_client, "Redis client is not initialized"
        return self.bot.redis_client

    @typing.override
    async def cog_check(self, ctx: commands.Context) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self.bot.redis_client:
            await ctx.send("Storage is not available, please try again later")
            return False

        if not ctx.guild:
            await ctx.send("This command can only be used in a server")
            return False

        return True


async def setup(bot: DiscordBot):
    """Add greeting cog."""
    await bot.add_cog(WelcomeFarewellCog(bot))
