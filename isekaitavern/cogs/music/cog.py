import typing

import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot
from isekaitavern.services.repository import RedisClient
from isekaitavern.utils.context_helper import fetch_guild, fetch_member

from .core import MusicClient, VocalGuildChannel


class MusicCog(commands.Cog, name="music"):
    def __init__(self, bot: DiscordBot) -> None:
        self.bot = bot
        self.__guild: dict[int, MusicClient] = {}

    @commands.hybrid_command()
    async def voice_status(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
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

        guild_client = self._require_guild_client(fetch_guild(ctx))
        await guild_client.join_channel(channel)

    @commands.command()
    async def play(self, ctx: commands.Context, url: str) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))

        if not guild_client.voice_client:
            # Bot is not in a voice channel
            author = fetch_member(ctx)
            if not author.voice or not author.voice.channel:
                # User is not in a voice channel
                await ctx.send("You are not connected to a voice channel")
                return
            # Bot will join the author's voice channel
            await guild_client.join_channel(author.voice.channel)

        await guild_client.add_to_playlist(url)

        await guild_client.play_music()

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: str | None = None) -> None:
        """Set the volume from 0 to 1000."""
        guild = self._require_guild_client(fetch_guild(ctx))
        if volume:
            guild.adjust_volume(volume)
            await ctx.send(f"Volume set to {guild.volume}")
        else:
            await ctx.send(f"Volume is {guild.volume}/1000")

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
        guild_client.stop()
        if guild_client.get_playlist_length() > 0:
            await guild_client.play_music()

    @commands.command()
    async def pause(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
        guild_client.pause()

    @commands.command()
    async def playlist(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
        playlist = guild_client.playlist
        msg = ""
        for i, music in enumerate(playlist):
            msg += f"{i+1}.[{music.title}]({music.url})\n"
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("Playlist is empty")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
        if not guild_client.current_playing:
            await ctx.send("No music is currently playing")
            return
        music = guild_client.current_playing
        await ctx.send(f"Now playing: [{music.title}]({music.url})")

    @commands.command()
    async def clear(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
        guild_client.clear_playlist()

    @commands.command()
    async def leave(self, ctx: commands.Context) -> None:
        guild_client = self._require_guild_client(fetch_guild(ctx))
        await guild_client.leave()

    @commands.Cog.listener()
    async def on_guild_remove(self, ctx: commands.Context) -> None:
        guild = fetch_guild(ctx)
        guild_client = self._require_guild_client(guild)
        guild_client.stop()
        del self.__guild[guild.id]

    @typing.override
    async def cog_check(self, ctx: commands.Context) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if not self.bot.redis_client:
            await ctx.send("Playlist is not available, music commands are disabled")
            return False

        if not ctx.guild:
            await ctx.send("This command can only be used in a server")
            return False

        return True

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.id != self.bot.application_id:
            return

        if before.channel is not None and after.channel is None:
            del self.__guild[member.guild.id]

    def _require_guild_client(self, guild: discord.Guild) -> MusicClient:
        if guild.id not in self.__guild:
            self.__guild[guild.id] = MusicClient(guild, self.bot.loop)
        return self.__guild[guild.id]

    @property
    def redis_client(self) -> RedisClient:
        assert self.bot.redis_client, "Redis is not available"
        return self.bot.redis_client


async def setup(bot: DiscordBot) -> None:
    """Add music play cog."""
    await bot.add_cog(MusicCog(bot))
