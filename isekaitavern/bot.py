import traceback
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
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix=lambda *_: (), intents=intents)

        self.agent = assistant_core.DiscordAgent(
            api_key=app_config.agent.token,
            base_url=app_config.agent.base_url,
            model=app_config.agent.model,
            language=app_config.bot.lang,
        )

    @typing.override
    async def setup_hook(self):
        await self.tree.sync()

    async def on_tree_error(self, _: discord.Interaction, error: discord.app_commands.AppCommandError):
        logger.error("".join(traceback.format_exception(error)))

    @typing.override
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not self.user:
            return
        if not message.guild:
            return
        if not message.channel or not isinstance(message.channel, discord.TextChannel):
            return
        if not message.author or not isinstance(message.author, discord.Member):
            return

        should_reply = self.user.mentioned_in(message)
        if not should_reply and message.reference:
            replied = message.reference.resolved

            if replied is None and message.reference.message_id:
                try:
                    replied = await message.channel.fetch_message(message.reference.message_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    replied = None

            should_reply = isinstance(replied, discord.Message) and replied.author.id == self.user.id

        if should_reply:
            logger.info(f"Message: {message.content}")
            res = await self.agent.run(
                self,
                message.guild,
                message.channel,
                message.author,
                message.content,
            )
            if res[0]:
                await message.reply(res[0])
