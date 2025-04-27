import discord
from discord.ext import commands


def fetch_guild(o: commands.Context | discord.Message | discord.Interaction) -> discord.Guild:
    """Ensure that the command is used in a guild context."""
    if not o.guild:
        raise commands.GuildNotFound("This command can only be used in a guild.")
    return o.guild


def fetch_member(o: commands.Context | discord.Message) -> discord.Member:
    """Ensure that the command is used by a member to a guild."""
    if not isinstance(o.author, discord.Member):
        raise commands.UserNotFound("This command can only be used by a member to a guild.")
    return o.author


def fetch_text_channel(o: commands.Context | discord.Message | discord.Interaction) -> discord.TextChannel:
    """Ensure that the command is used in a text channel."""
    if not isinstance(o.channel, discord.TextChannel):
        raise commands.ChannelNotFound("This command can only be used in a text channel.")
    return o.channel


