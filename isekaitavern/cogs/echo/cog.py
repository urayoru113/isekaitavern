from discord.ext import commands

from isekaitavern.bot import DiscordBot


class Echo(commands.Cog, name="echo"):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx: commands.Context, *args):
        await ctx.send(*args)


async def setup(bot: DiscordBot):
    """Add echo cog."""
    await bot.add_cog(Echo(bot))
