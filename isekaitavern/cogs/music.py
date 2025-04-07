import asyncio
import dataclasses
import typing

import discord
import redis.asyncio as redis
import yt_dlp
from discord.ext import commands

from isekaitavern import errno
from isekaitavern.bot import DiscordBot
from isekaitavern.config.ffmpeg import FFMPEG_OPTIONS
from isekaitavern.config.youtube import YDL_OPTS
from isekaitavern.utils.context_helper import fetch_guild, fetch_member
from isekaitavern.utils.logging import logger
from isekaitavern.utils.tool import B64

VocalGuildChannel = discord.VoiceChannel | discord.StageChannel


@dataclasses.dataclass
class MusicInfo:
    title: str
    stream_url: str
    url: str
    description: str


class GuildClient:
    __expire_time: int = 60 * 60 * 24
    __volume: int = 20
    __current_playing: MusicInfo | None = None
    __ydl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(YDL_OPTS)

    voice_client: discord.VoiceClient | None = None

    def __init__(self, guild: discord.Guild, redis: redis.Redis, loop: asyncio.AbstractEventLoop):
        self.guild = guild
        self.redis = redis
        self.loop = loop

        self.__playlist_key = f"{guild.id}:playlist"

    async def join_channel(self, channel: VocalGuildChannel) -> None:
        if not self.voice_client:
            self.voice_client = await channel.connect()
        else:
            await self.voice_client.move_to(channel)

    async def play_music(self):
        if not self.voice_client:
            raise errno.StatusError("Not connected to a voice channel")

        if self.voice_client.is_playing():
            logger.info("Voice client is already playing")
            return

        if self.voice_client.is_paused():
            self.voice_client.resume()
            return

        if not await self.get_playlist_length():
            logger.info("Playlist is empty")
            return

        self.__current_playing = await self.pop_from_playlist()

        self.source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(self.__current_playing.stream_url, **FFMPEG_OPTIONS),
            self.__volume / 100,
        )
        self.voice_client.play(self.source, after=self.__after)

    def __after(self, error: Exception | None):
        self.__current_playing = None
        if error:
            logger.error(f"An error occurred: {error}")
        self.loop.create_task(self.play_music())

    async def adjust_volume(self, volume: str) -> None:
        if not volume.isdigit():
            raise errno.ValueError("Volume must be a number")

        volume_int = int(volume)

        if volume_int > 100:
            volume_int = 100

        if volume_int < 0:
            volume_int = 0

        self.__volume = volume_int

        if not self.voice_client:
            return

        if not self.voice_client.source:
            return

        self.source.volume = volume_int / 100

    async def stop(self) -> None:
        if not self.voice_client:
            return
        self.voice_client.stop()

    async def pause(self) -> None:
        if not self.voice_client:
            return
        self.voice_client.pause()

    async def leave(self) -> None:
        if self.voice_client:
            await self.voice_client.disconnect()

    async def add_to_playlist(self, *urls: str) -> None:
        tasks = (
            self.loop.run_in_executor(None, lambda url=url: self.__ydl.extract_info(url, download=False))
            for url in urls
        )
        infos = await asyncio.gather(*tasks)
        for url, info in zip(urls, infos, strict=True):
            assert info
            music_info = MusicInfo(
                url=url,
                stream_url=info["url"],
                title=info["title"],
                description=info["description"],
            )
            value = B64.encode(**dataclasses.asdict(music_info))
            await self.redis.rpush(self.__playlist_key, value)
        await self.redis.expire(self.__playlist_key, self.__expire_time)

    async def pop_from_playlist(self) -> MusicInfo:
        logger.info("Popping from playlist")
        out = await self.redis.lpop(self.__playlist_key)
        await self.redis.expire(self.__playlist_key, self.__expire_time)
        if not out:
            raise errno.ValueError("Playlist is empty")
        return MusicInfo(**B64.decode(out))

    async def get_playlist(self) -> list[MusicInfo]:
        await self.redis.expire(self.__playlist_key, self.__expire_time)
        return [MusicInfo(**B64.decode(x)) for x in await self.redis.lrange(self.__playlist_key, 0, -1)]

    async def clear_playlist(self) -> None:
        await self.redis.delete(self.__playlist_key)

    async def get_playlist_length(self) -> int:
        await self.redis.expire(self.__playlist_key, self.__expire_time)
        return await self.redis.llen(self.__playlist_key)

    @property
    def volume(self) -> int:
        return self.__volume

    @property
    def current_playing(self) -> MusicInfo | None:
        return self.__current_playing


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
