import discord
from discord.ext import commands


def fetch_guild(ctx: commands.Context | discord.Message) -> discord.Guild:
    """Ensure that the command is used in a guild context."""
    if not ctx.guild:
        raise commands.GuildNotFound("This command can only be used in a guild.")
    return ctx.guild


def fetch_member(o: commands.Context | discord.Message) -> discord.Member:
    """Ensure that the command is used by a member to a guild."""
    if not isinstance(o.author, discord.Member):
        raise commands.UserNotFound("This command can only be used by a member to a guild.")
    return o.author
