import asyncio
import random
from collections import deque

import discord
import yt_dlp

from isekaitavern import errno
from isekaitavern.config.ffmpeg import FFMPEG_OPTIONS
from isekaitavern.config.youtube import YDL_OPTS
from isekaitavern.types import VocalGuildChannel
from isekaitavern.utils.logging import logger
from isekaitavern.utils.url import extract_youtube_url

from .model import MusicInfo


class Playlist(deque[MusicInfo]):
    def __init__(self, maxlen):
        super().__init__(maxlen=maxlen)

    def shuffle(self):
        random.shuffle(self)

    def pop(self) -> MusicInfo:
        return super().pop()

    def push(self, item: MusicInfo) -> None:
        self.appendleft(item)

    def delete(self, index: int) -> None:
        del self[index]


class MusicClient:
    __volume: int = 100
    __current_playing: MusicInfo | None = None
    __ydl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(YDL_OPTS)

    voice_client: discord.VoiceClient | None = None

    __playlist = Playlist(maxlen=100)

    def __init__(self, guild: discord.Guild, loop: asyncio.AbstractEventLoop):
        self.guild = guild
        self.loop = loop

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

        if not self.get_playlist_length():
            logger.info("Playlist is empty")
            return

        self.__current_playing = self.pop_from_playlist()

        self.source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(self.__current_playing.stream_url, **FFMPEG_OPTIONS),
            self.__volume / 1000,
        )
        self.voice_client.play(self.source, after=self.__after)

    def __after(self, error: Exception | None):
        self.__current_playing = None
        if error:
            logger.error(f"An error occurred: {error}")
        self.loop.create_task(self.play_music())

    def adjust_volume(self, volume: str) -> None:
        if not volume.isdigit():
            raise errno.ValueError("Volume must be a number")

        volume_int = int(volume)

        if volume_int > 1000:
            volume_int = 1000

        if volume_int < 0:
            volume_int = 0

        self.__volume = volume_int

        if not self.voice_client:
            return

        if not self.voice_client.source:
            return

        self.source.volume = volume_int / 1000

    def stop(self) -> None:
        if not self.voice_client:
            return
        self.voice_client.stop()

    def pause(self) -> None:
        if not self.voice_client:
            return
        self.voice_client.pause()

    async def leave(self) -> None:
        if self.voice_client:
            await self.voice_client.disconnect()

    async def add_to_playlist(self, url: str) -> None:
        logger.info(f"add {url} to playlist")
        info = await self.loop.run_in_executor(
            None,
            lambda url=url: self.__ydl.extract_info(extract_youtube_url(url), download=False),
        )
        assert info, f"Failed to extract info from url: {url}"
        music_info = MusicInfo(
            url=url,
            stream_url=info["url"],
            title=info["title"],
            description=info["description"],
        )
        self.__playlist.push(music_info)

    def pop_from_playlist(self) -> MusicInfo:
        logger.info("Popping from playlist")
        return self.__playlist.pop()

    def clear_playlist(self) -> None:
        self.__playlist.clear()

    def get_playlist_length(self) -> int:
        return len(self.__playlist)

    @property
    def volume(self) -> int:
        return self.__volume

    @property
    def current_playing(self) -> MusicInfo | None:
        return self.__current_playing

    @property
    def playlist(self) -> list[MusicInfo]:
        return list(self.__playlist)
