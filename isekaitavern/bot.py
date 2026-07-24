import typing

import assistant_core
import discord
import discord.ext.commands as commands

from .config import app_config
from .utils.logging import logger


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        logger.info("Initializing bot")
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=lambda *_: (), intents=intents)

        self.agents: dict[int, assistant_core.DiscordAgent] = {}  # [guild_id, agent]

    @typing.override
    async def on_message(self, message: discord.Message):  # noqa: PLR0912
        if not message.guild:
            return
        if message.author.bot:
            return
        if not self.user:
            return
        if not message.channel or not isinstance(message.channel, discord.TextChannel):
            return
        if not message.author or not isinstance(message.author, discord.Member):
            return

        should_reply = self.user.mentioned_in(message)

        if not should_reply:
            bot_member = message.guild.get_member(self.user.id)

            if bot_member:
                bot_role_ids = {role.id for role in bot_member.roles}
                should_reply = any(role.id in bot_role_ids for role in message.role_mentions)

        if not should_reply and message.reference:
            replied = message.reference.resolved

            if replied is None and message.reference.message_id:
                try:
                    replied = await message.channel.fetch_message(message.reference.message_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    replied = None

            should_reply = isinstance(replied, discord.Message) and replied.author.id == self.user.id

        if should_reply:
            if message.guild.id not in app_config.bot.allowed_guilds:
                replied_message = (
                    "此機器人僅開放白名單伺服器使用，如需加入白名單，請聯絡開發者。"
                    if app_config.bot.lang == "zh-TW"
                    else "This bot is only available in approved servers. Please contact the developer to request access."
                )
                await message.reply(replied_message)
                return

            if message.guild.id not in self.agents:
                self.agents[message.guild.id] = assistant_core.DiscordAgent(
                    api_key=app_config.agent_token,
                    api=app_config.bot.api,
                    model=app_config.bot.model,
                    base_url=app_config.agent_base_url,
                    language=app_config.bot.lang,  # type:ignore
                    web_search_endpoint=app_config.search_endpoint,
                    timezone=app_config.bot.timezone,
                )

            logger.info(f"Message: {message.content}")
            res = await self.agents[message.guild.id].run(
                self,
                message.guild,
                message.channel,
                message.author,
            )
            if res[0]:
                await message.reply(res[0])
