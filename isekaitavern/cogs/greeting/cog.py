import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot


class Greeting(commands.Cog, name="greeting"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f"Welcome @{member.name}")


async def setup(bot: DiscordBot):
    """Add greeting cog."""
    await bot.add_cog(Greeting(bot))
