import asyncio
import typing

import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.utils.context_helper import fetch_guild, fetch_member, fetch_text_channel
from isekaitavern.utils.helpers import channel_id_to_name
from isekaitavern.utils.logging import logger

from .core import Anonymous
from .model import AnonymousMemberModel, AnonymousSettingsModel


class AnonymousCog(commands.Cog, Anonymous, name="anonymous"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.bot._register_beanie_model(
            self.bot.motor_client.GuildSettings,
            AnonymousMemberModel,
            AnonymousSettingsModel,
        )

    @commands.hybrid_group(aliases=["anon"])
    async def anonymous(self, _: commands.Context): ...

    @anonymous.command(name="set")
    async def set(self, ctx: commands.Context, nickname: str, avatar_url: str):
        # if not ctx.interaction:
        #    # This command is only available in slash commands
        #    return
        guild = fetch_guild(ctx)
        member = fetch_member(ctx)
        await self.set_anonymous_member(guild.id, member.id, nickname, avatar_url)
        embed = discord.Embed()
        embed.set_author(name=nickname, icon_url=avatar_url)
        await ctx.reply(embed=embed, ephemeral=True)

    @anonymous.command(name="send")
    async def send(self, ctx: commands.Context, msg: str):
        guild = fetch_guild(ctx)
        member = fetch_member(ctx)
        channel = fetch_text_channel(ctx)
        anonymous_settings, anonymous_member, webhooks = await asyncio.gather(
            AnonymousSettingsModel.find_one(AnonymousSettingsModel.guild_id == guild.id),
            AnonymousMemberModel.find_by_indexed(guild.id, member.id),
            channel.webhooks(),
        )
        if not anonymous_settings or not anonymous_settings.enabled:
            return
        if channel.id not in anonymous_settings.channel_ids:
            logger.info(f"Channel {channel.id} is not in anonymous channels: {anonymous_settings.channel_ids}")
            return
        webhook = discord.utils.get(webhooks, name="isekaitavern anonymous bot")
        if not webhook:
            logger.info("Webhook not found")
            return
        if not anonymous_member:
            logger.info("Anonymous member model not found")
            return
        await webhook.send(msg, username=anonymous_member.nickname, avatar_url=anonymous_member.avatar_url)

    @anonymous.command()
    async def add_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild = fetch_guild(ctx)
        await self.add_anonymous_channel(guild.id, channel.id)
        webhook = discord.utils.get(await channel.webhooks(), name="isekaitavern anonymous bot")
        if not webhook:
            await channel.create_webhook(name="isekaitavern anonymous bot")
            logger.info(f"Add anonymous for channel {channel.id}")
        else:
            logger.info(f"Webhook already exists for channel {channel.id}")

    @anonymous.command()
    async def remove_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild = fetch_guild(ctx)
        await self.remove_anonymous_channel(guild.id, channel.id)
        webhook = discord.utils.get(await channel.webhooks(), name="isekaitavern anonymous bot")
        if webhook:
            await webhook.delete()
            logger.info(f"Remove anonymous for channel {channel.id}")
        else:
            logger.info(f"Webhook not found for channel {channel.id}")

    @anonymous.command()
    async def list_channels(self, ctx: commands.Context):
        guild = fetch_guild(ctx)
        model = await AnonymousSettingsModel.find_one(AnonymousSettingsModel.guild_id == guild.id)
        if model and model.channel_ids:
            await ctx.send(str(*(channel_id_to_name(channel) for channel in model.channel_ids)))
        else:
            await ctx.send("No anonymous channels found.")

    @anonymous.command()
    async def enable(self, ctx: commands.Context):
        guild = fetch_guild(ctx)
        await self.set_anonymous_settings(guild.id, enable=True)
        logger.info(f"Enable anonymous for guild {guild.id}")

    @anonymous.command()
    async def disable(self, ctx: commands.Context):
        guild = fetch_guild(ctx)
        await self.set_anonymous_settings(guild.id, enable=False)
        logger.info(f"Disable anonymous for guild {guild.id}")

    @typing.override
    async def cog_check(self, ctx: commands.Context) -> bool:  # type: ignore
        if not self.bot.redis_client:
            return False

        return bool(ctx.guild)


async def setup(bot: DiscordBot):
    """Add anonymous cog."""
    await bot.add_cog(AnonymousCog(bot))
