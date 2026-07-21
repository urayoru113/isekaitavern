import random

import discord
from discord import app_commands
from discord.ext import commands

from ...bot import DiscordBot
from ...i18n import i18n
from ...utils.logging import logger


class GiveawayCog(commands.Cog):
    def __init__(self, bot: DiscordBot):
        logger.info("Initializing GiveawayCog")
        self.bot = bot

    giveaway_group = app_commands.Group(name="giveaway", description="身分組抽獎系統")

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @giveaway_group.command(name="role", description="從指定身分組中隨機抽取成員")
    @app_commands.describe(role="選擇要抽獎的身分組", num="抽取人數")
    async def giveaway_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        num: int,
    ):
        if num <= 0:
            embed = discord.Embed(
                description=i18n.get("zh-tw", "commands.giveaway.invalid_count"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        members = [m for m in role.members if not m.bot]

        if not members:
            embed = discord.Embed(
                description=i18n.get("zh-tw", "commands.giveaway.empty_role"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if num > len(members):
            embed = discord.Embed(
                description=i18n.get(
                    "zh-tw",
                    "commands.giveaway.not_enough_members",
                    count=len(members),
                    num=num,
                ),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        winners = random.sample(members, num)

        embed = discord.Embed(
            title=i18n.get("zh-tw", "commands.giveaway.title", role=role.name),
            color=discord.Color.gold(),
        )
        winner_text = "\n".join(f"{i + 1}. {w.mention}" for i, w in enumerate(winners))
        embed.add_field(
            name=i18n.get("zh-tw", "commands.giveaway.winners", count=len(winners)),
            value=winner_text,
            inline=False,
        )
        embed.set_footer(text=f"身分組：{role.name} | 總人數：{len(members)}")

        await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @giveaway_group.command(name="list", description="列出指定身分組的所有成員")
    @app_commands.describe(role="選擇要查看的身分組")
    async def giveaway_list(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ):
        members = [m for m in role.members if not m.bot]

        if not members:
            embed = discord.Embed(
                description=i18n.get("zh-tw", "commands.giveaway.empty_role"),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=i18n.get("zh-tw", "commands.giveaway.list_title", role=role.name, count=len(members)),
            color=discord.Color.blue(),
        )
        member_text = "\n".join(f"{i + 1}. {m.mention}" for i, m in enumerate(members))
        embed.add_field(
            name=i18n.get("zh-tw", "commands.giveaway.list_members"),
            value=member_text,
            inline=False,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: DiscordBot):
    cog = GiveawayCog(bot)
    await bot.add_cog(cog)
