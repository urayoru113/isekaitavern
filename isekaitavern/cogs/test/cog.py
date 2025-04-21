import discord
from discord.ext import commands

from isekaitavern.bot import DiscordBot


class Test(commands.Cog, name="test"):
    help: str = "embed <msg> <title> <description"

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def channel(self, ctx: commands.Context, msg: discord.TextChannel):
        print(msg)
        print(type(msg))
        print(msg.name)
        print(msg.id)
        await msg.send("NB")


async def setup(bot: DiscordBot):
    """Add echo cog."""
    await bot.add_cog(Test(bot))
