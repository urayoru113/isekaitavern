import contextlib
import typing

import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.enums import Color
from isekaitavern.utils.context_helper import fetch_guild, fetch_member

from .core import WelcomeFarewell
from .model import FarewellModel, WelcomeFarewellModel_T, WelcomeModel


class WelcomeFarewellCog(commands.Cog, name="guild_settings"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.bot._register_beanie_model(self.bot.motor_client.GuildSettings, WelcomeModel, FarewellModel)
        self.guild_client = WelcomeFarewell()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self._on_event(WelcomeModel, member)

    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member) -> None:
        await self._on_event(FarewellModel, member)

    @commands.hybrid_group()
    async def welcome(self, _: commands.Context): ...

    @commands.hybrid_group()
    async def farewell(self, _: commands.Context): ...

    @welcome.command(name="message")
    async def welcome_message(self, ctx: commands.Context, channel: discord.TextChannel, title: str, *, message: str):
        await self._set_msg(WelcomeModel, ctx, channel, title, message)

    @farewell.command(name="message")
    async def farewell_message(self, ctx: commands.Context, channel: discord.TextChannel, title: str, *, message: str):
        await self._set_msg(FarewellModel, ctx, channel, title, message)

    @welcome.command(name="color")
    async def welcome_color(self, ctx: commands.Context, color: str) -> None:
        await self._set_color(ctx, WelcomeModel, color)

    @farewell.command(name="color")
    async def farewell_color(self, ctx: commands.Context, color: str) -> None:
        await self._set_color(ctx, FarewellModel, color)

    @welcome.command(name="thumbnail")
    async def welcome_thumbnail(self, ctx: commands.Context, url: str = "") -> None:
        await self._set_thumbnail(ctx, WelcomeModel, url)

    @farewell.command(name="thumbnail")
    async def farewell_thumbnail(self, ctx: commands.Context, url: str = "") -> None:
        await self._set_thumbnail(ctx, FarewellModel, url)

    @welcome.command(name="image")
    async def welcome_image(self, ctx: commands.Context, url: str = "") -> None:
        await self._set_image(ctx, WelcomeModel, url)

    @farewell.command(name="image")
    async def farewell_image(self, ctx: commands.Context, url: str = "") -> None:
        await self._set_image(ctx, FarewellModel, url)

    async def _set_color(
        self,
        ctx: commands.Context,
        model_cls: type[WelcomeFarewellModel_T],
        maybe_color: str,
    ) -> None:
        set_by_member = fetch_member(ctx)
        with contextlib.suppress(ValueError):
            maybe_color = Color.from_str(maybe_color.upper()).value

        try:
            color_hex = discord.Color.from_str(maybe_color).value
        except ValueError:
            await ctx.send("Invalid color name or hex code")
            return

        guild = fetch_guild(ctx)
        model = await self.guild_client.set_welcome_farewell_model(
            model_cls,
            guild.id,
            set_by_member_id=set_by_member.id,
            color=color_hex,
        )
        embed = self._get_embed(
            model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        reply_content = "Updated frame color successfully\n"
        if not model.channel_id:
            reply_content += "### Please set the channel first\n"
        reply_content += f"{model_cls.__name__} message:\n"
        await ctx.reply(reply_content, embed=embed)

    async def _set_thumbnail(
        self,
        ctx: commands.Context,
        model_cls: type[WelcomeFarewellModel_T],
        url: str = "",
    ) -> None:
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        model = await self.guild_client.set_welcome_farewell_model(
            model_cls,
            guild.id,
            set_by_member_id=set_by_member.id,
            thumbnail_url=url,
        )
        embed = self._get_embed(
            model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )
        reply_content = "Updated thumbnail successfully\n"
        if not model.channel_id:
            reply_content += "### Please set the channel first\n"
        reply_content += f"{model_cls.__name__} message:\n"
        await ctx.reply(reply_content, embed=embed)

    async def _set_image(self, ctx: commands.Context, model_cls: type[WelcomeFarewellModel_T], url: str = "") -> None:
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        model = await self.guild_client.set_welcome_farewell_model(
            model_cls,
            guild.id,
            set_by_member_id=set_by_member.id,
            image_url=url,
        )
        embed = self._get_embed(
            model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )

        reply_content = "Updated image successfully\n"
        if not model.channel_id:
            reply_content += "### Please set the channel first\n"
        reply_content += f"{model_cls.__name__} message:\n"

        await ctx.reply(reply_content, embed=embed)

    async def _set_msg(
        self,
        model_cls: type[WelcomeFarewellModel_T],
        ctx: commands.Context,
        channel: discord.TextChannel,
        title: str,
        msg: str,
    ):
        guild = fetch_guild(ctx)
        set_by_member = fetch_member(ctx)
        model = await self.guild_client.set_welcome_farewell_model(
            model_cls,
            guild.id,
            set_by_member_id=set_by_member.id,
            channel_id=channel.id,
            title=title,
            msg=msg,
        )

        embed = self._get_embed(
            model,
            member=f"<@{set_by_member.id}>",
            member_icon=set_by_member.display_avatar.url,
            member_banner=set_by_member.display_banner.url if set_by_member.display_banner else "",
        )

        await ctx.reply(f"Updated {model_cls.__name__} message successfully\nmessage:\n", embed=embed)

    async def _on_event(self, model_cls: type[WelcomeFarewellModel_T], member: discord.Member) -> None:
        model = await self.guild_client.get_welcome_farewell_model(model_cls, member.guild.id)

        if not model or not model.enabled:
            return

        channel = discord.utils.get(member.guild.channels, id=model.channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return

        embed = self._get_embed(
            model,
            member=f"<@{member.id}>",
            member_icon=member.display_avatar.url,
            member_banner=member.display_banner.url if member.display_banner else "",
        )

        await channel.send(embed=embed)

    def _get_embed(self, model: WelcomeFarewellModel_T, **format_kwargs: str) -> discord.Embed:
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

    @typing.override
    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore
        return bool(ctx.guild)


async def setup(bot: DiscordBot):
    """Add greeting cog."""
    await bot.add_cog(WelcomeFarewellCog(bot))
