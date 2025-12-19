import typing

import discord

VocalGuildChannel = discord.VoiceChannel | discord.StageChannel
User = discord.Member | discord.User


class SupportsStr(typing.Protocol):
    def __str__(self) -> str: ...
