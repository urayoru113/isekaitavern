import asyncio
import json

import discord
import yt_dlp

from isekaitavern import errno
from isekaitavern.config.ffmpeg import FFMPEG_OPTIONS
from isekaitavern.config.youtube import YDL_OPTS
from isekaitavern.services.repository import RedisClient
from isekaitavern.utils.logging import logger

from .model import MusicInfo

VocalGuildChannel = discord.VoiceChannel | discord.StageChannel


class GuildClient:
    __volume: int = 20
    __current_playing: MusicInfo | None = None
    __ydl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(YDL_OPTS)

    voice_client: discord.VoiceClient | None = None

    def __init__(self, guild: discord.Guild, redis_client: RedisClient, loop: asyncio.AbstractEventLoop):
        self.guild = guild
        self.redis_client = redis_client
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
        logger.info(f"add {urls} to playlist")
        tasks = (
            self.loop.run_in_executor(None, lambda url=url: self.__ydl.extract_info(url, download=False))
            for url in urls
        )
        infos = await asyncio.gather(*tasks)
        for url, info in zip(urls, infos, strict=True):
            assert info, "Failed to extract info"
            music_info = MusicInfo(
                url=url,
                stream_url=info["url"],
                title=info["title"],
                description=info["description"],
            )
            value = json.dumps(music_info.to_dict())
            await self.redis_client.rpush(self.__playlist_key, value)

    async def pop_from_playlist(self) -> MusicInfo:
        logger.info("Popping from playlist")
        out = await self.redis_client.lpop(self.__playlist_key)
        if not isinstance(out, str):
            raise errno.ValueError("Playlist is empty")
        return MusicInfo.from_dict(json.loads(out))

    async def get_playlist(self) -> list[MusicInfo]:
        return [MusicInfo.from_dict(json.loads(x)) for x in await self.redis_client.lrange(self.__playlist_key, 0, -1)]

    async def clear_playlist(self) -> None:
        await self.redis_client.redis.delete(self.__playlist_key)

    async def get_playlist_length(self) -> int:
        return await self.redis_client.llen(self.__playlist_key)

    @property
    def volume(self) -> int:
        return self.__volume

    @property
    def current_playing(self) -> MusicInfo | None:
        return self.__current_playing
