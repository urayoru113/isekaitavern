import discord
from discord.ext import commands


def fetch_guild(o: commands.Context | discord.Message) -> discord.Guild:
    """Ensure that the command is used in a guild context."""
    if not o.guild:
        raise commands.GuildNotFound("This command can only be used in a guild.")
    return o.guild


def fetch_member(o: commands.Context | discord.Message) -> discord.Member:
    """Ensure that the command is used by a member to a guild."""
    if not isinstance(o.author, discord.Member):
        raise commands.UserNotFound("This command can only be used by a member to a guild.")
    return o.author


#def get_channel_by_id(guild: discord.Guild, id: int) -> discord.guild.GuildChannel | None:
#    """Get a channel by its ID."""
#    for channel in guild.channels:
#        if channel.id == id:
#            return channel
#    return None
