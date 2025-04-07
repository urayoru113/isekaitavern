import typing

import discord
import redis.asyncio as redis
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.utils.context_helper import fetch_guild, fetch_member

from .core import GuildClient, VocalGuildChannel


class MusicCog(commands.Cog, name="music"):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot = bot
        self.__guild: dict[int, GuildClient] = {}

    @commands.hybrid_command()
    async def voice_status(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        client = guild_client.voice_client
        msg = ""
        if client:
            msg += f"bot is connected: {client.is_connected()}\n"
            msg += f"bot is playing: {client.is_playing()}"
            msg += f"bot is paused: {client.is_paused()}"
            if guild_client.current_playing:
                msg += f"Playing title: {guild_client.current_playing.title}:{guild_client.current_playing.url}\n"
        msg += f"volume: {guild_client.source.volume}"
        await ctx.send(msg, ephemeral=True)

    @commands.command()
    async def join(self, ctx: commands.Context, *, channel: VocalGuildChannel | None = None) -> None:
        if not channel:
            # if no channel is specified, join the author's voice channel
            author = fetch_member(ctx)
            if not author.voice or not author.voice.channel:
                # User is not in a voice channel
                await ctx.send("You are not connected to a voice channel")
                return
            channel = author.voice.channel

        guild_client = self._get_guild_client(fetch_guild(ctx))
        await guild_client.join_channel(channel)

    @commands.command()
    async def play(self, ctx: commands.Context, *urls: str) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))

        if not guild_client.voice_client:
            # Bot is not in a voice channel
            author = fetch_member(ctx)
            if not author.voice or not author.voice.channel:
                # User is not in a voice channel
                await ctx.send("You are not connected to a voice channel")
                return
            # Bot will join the author's voice channel
            await guild_client.join_channel(author.voice.channel)

        if urls:
            await guild_client.add_to_playlist(*urls)

        await guild_client.play_music()

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: str | None = None) -> None:
        guild = self._get_guild_client(fetch_guild(ctx))
        if volume:
            await guild.adjust_volume(volume)
            await ctx.send(f"Volume set to {guild.volume}%")
        else:
            await ctx.send(f"Volume set to {guild.volume}%")

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        await guild_client.stop()
        if await guild_client.get_playlist_length() > 0:
            await guild_client.play_music()

    @commands.command()
    async def pause(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        await guild_client.pause()

    @commands.command()
    async def playlist(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        playlist = await guild_client.get_playlist()
        msg = ""
        for i, music in enumerate(playlist):
            msg += f"{i+1}.[{music.title}]({music.url})\n"
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("Playlist is empty")

    @commands.command()
    async def nowplaying(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        if not guild_client.current_playing:
            await ctx.send("No music is currently playing")
            return
        music = guild_client.current_playing
        await ctx.send(f"Now playing: [{music.title}]({music.url})")

    @commands.command()
    async def clear(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        await guild_client.clear_playlist()

    @commands.command()
    async def leave(self, ctx: commands.Context) -> None:
        guild_client = self._get_guild_client(fetch_guild(ctx))
        await guild_client.leave()

    @typing.override
    async def cog_check(self, ctx: commands.Context) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self.bot.redis:
            await ctx.send("Playlist is not available, music commands are disabled")
            return False

        if not ctx.guild:
            await ctx.send("This command can only be used in a server")
            return False

        return True

    @property
    def redis(self) -> redis.Redis:
        assert self.bot.redis
        return self.bot.redis

    def _get_guild_client(self, guild: discord.Guild) -> GuildClient:
        if guild.id not in self.__guild:
            self.__guild[guild.id] = GuildClient(guild, self.redis, self.bot.loop)
        return self.__guild[guild.id]

    @commands.Cog.listener()
    async def on_guild_remove(self, ctx: commands.Context) -> None:
        guild = fetch_guild(ctx)
        await self.redis.delete(f"{guild.id}:playlist")
        del self.__guild[guild.id]


async def setup(bot: DiscordBot) -> None:
    """Add music play cog."""
    await bot.add_cog(MusicCog(bot))
