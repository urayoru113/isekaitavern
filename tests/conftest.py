import asyncio
from unittest.mock import AsyncMock

import beanie
import discord
import pytest
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

from isekaitavern.bot import DiscordBot
from isekaitavern.cogs.anonymous.cog import AnonymousCog
from isekaitavern.cogs.anonymous.model import AnonymousBaseSettings, AnonymousUserSettings
from isekaitavern.config import app_config


# Shared event loop for session-scoped fixtures
_loop = None


def _get_loop():
    global _loop
    if _loop is None:
        _loop = asyncio.new_event_loop()
    return _loop


@pytest.fixture(scope="function")
def mongo_client():
    return AsyncIOMotorClient(app_config.database.mongo_url)


@pytest.fixture(scope="function")
def db(mongo_client):
    return mongo_client.GuildSettings


@pytest.fixture(scope="function")
def redis_client():
    return redis.Redis.from_url(app_config.database.redis_url, decode_responses=True)


@pytest.fixture(scope="function", autouse=True)
async def init_beanie(db):
    await beanie.init_beanie(db, document_models=[AnonymousBaseSettings, AnonymousUserSettings])


@pytest.fixture
async def clean_db(db, redis_client):
    await db.anonymous_config.delete_many({})
    await db.anonymous_user_settings.delete_many({})
    await redis_client.flushdb()


@pytest.fixture
def mock_bot(mongo_client, redis_client):
    bot = AsyncMock(spec=DiscordBot)
    bot.motor_client = mongo_client
    bot.redis = redis_client
    bot.init_beanie = AsyncMock()
    bot._register_beanie_model = lambda *args: None
    return bot


@pytest.fixture
def cog(mock_bot):
    return AnonymousCog(mock_bot)


@pytest.fixture
def make_interaction():
    def _make():
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild = AsyncMock()
        interaction.guild.id = 123456
        interaction.guild_id = 123456
        interaction.user = AsyncMock()
        interaction.user.id = 987654
        interaction.channel = AsyncMock(spec=discord.TextChannel)
        interaction.channel.id = 111111
        interaction.response = AsyncMock()
        interaction.followup = AsyncMock()
        return interaction
    return _make


@pytest.fixture
def make_channel():
    def _make(channel_id=111111):
        channel = AsyncMock(spec=discord.TextChannel)
        channel.id = channel_id
        channel.mention = f"<#{channel_id}>"
        channel.webhooks = AsyncMock(return_value=[])
        channel.create_webhook = AsyncMock()
        return channel
    return _make


@pytest.fixture
def make_member():
    def _make(member_id=987654):
        member = AsyncMock(spec=discord.Member)
        member.id = member_id
        member.mention = f"<@{member_id}>"
        return member
    return _make


@pytest.fixture
def make_webhook():
    def _make(webhook_id=123, token="token"):
        webhook = AsyncMock(spec=discord.Webhook)
        webhook.id = webhook_id
        webhook.token = token
        webhook.send = AsyncMock()
        webhook.delete = AsyncMock()
        return webhook
    return _make