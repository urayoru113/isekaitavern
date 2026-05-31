import pytest
from isekaitavern.cogs.anonymous.model import AnonymousBaseSettings


async def test_smoke_cog_instantiation(cog):
    """Verify cog fixture creates AnonymousCog with real repo and service."""
    assert cog.repo is not None
    assert cog.service is not None
    # Verify redis is real (has ping method)
    assert hasattr(cog.repo.redis, "ping")


def test_smoke_interaction_mock(make_interaction):
    """Verify make_interaction creates valid interaction mock."""
    interaction = make_interaction()
    assert interaction.guild.id == 123456
    assert interaction.user.id == 987654
    assert interaction.channel.id == 111111
    assert callable(interaction.response.send_message)
    assert callable(interaction.response.defer)
    assert callable(interaction.followup.send)


async def test_smoke_callback_enable(cog, make_interaction):
    """Verify anonymous_enable calls send_message (no ephemeral kwarg - defaults to False)."""
    interaction = make_interaction()
    await cog.anonymous_enable.callback(cog, interaction)
    interaction.response.send_message.assert_called_once()
    # ephemeral is NOT passed in anonymous_enable (default=False)
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert "ephemeral" not in call_kwargs


async def test_smoke_db_write(cog, make_interaction):
    """Verify enable writes to DB correctly."""
    interaction = make_interaction()
    await cog.anonymous_enable.callback(cog, interaction)
    # Query DB
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is not None
    assert result.enabled is True


async def test_smoke_redis(cog):
    """Verify real Redis works and cog uses it."""
    redis = cog.repo.redis
    await redis.set("test_key", "test_value")
    result = await redis.get("test_key")
    assert result == "test_value"
