from unittest.mock import AsyncMock

import discord
import pytest

from isekaitavern.cogs.anonymous.model import AnonymousBaseSettings, AnonymousUserSettings, AnonymousWebhookInfo


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
    assert "ephemeral" in call_kwargs


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


# ========================================
# User Command Tests: icon
# ========================================


async def test_anonymous_icon(cog, make_interaction, clean_db):
    """Set anonymous icon URL and verify DB update + ephemeral response."""
    interaction = make_interaction()
    await cog.anonymous_icon.callback(cog, interaction, icon="https://example.com/avatar.png")

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert call_kwargs["ephemeral"] is True

    result = await AnonymousUserSettings.find_one(
        AnonymousUserSettings.guild_id == 123456, AnonymousUserSettings.user_id == 987654
    )
    assert result is not None
    assert result.avatar_url == "https://example.com/avatar.png"


async def test_anonymous_icon_invalid_url(cog, make_interaction, clean_db):
    """Icon command validates URLs — invalid URL is rejected with error message."""
    interaction = make_interaction()
    await cog.anonymous_icon.callback(cog, interaction, icon="not-a-url")

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert call_kwargs["ephemeral"] is True

    # Invalid URL should NOT be stored — no user settings created
    result = await AnonymousUserSettings.find_one(
        AnonymousUserSettings.guild_id == 123456, AnonymousUserSettings.user_id == 987654
    )
    assert result is None


# ========================================
# User Command Tests: name
# ========================================


async def test_anonymous_name(cog, make_interaction, clean_db):
    """Set anonymous display name and verify DB update + ephemeral response."""
    interaction = make_interaction()
    await cog.anonymous_name.callback(cog, interaction, name="Shadow")

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert call_kwargs["ephemeral"] is True

    result = await AnonymousUserSettings.find_one(
        AnonymousUserSettings.guild_id == 123456, AnonymousUserSettings.user_id == 987654
    )
    assert result is not None
    assert result.display_name == "Shadow"


async def test_anonymous_name_guild_none(cog, make_interaction, clean_db):
    """Name command returns early when guild is None — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_name.callback(cog, interaction, name="Shadow")

    interaction.response.send_message.assert_not_called()


# ========================================
# User Command Tests: preview
# ========================================


async def test_anonymous_preview(cog, make_interaction, clean_db):
    """Preview shows embed with user's configured anonymous settings."""
    interaction = make_interaction()
    await cog.repo.set_user_settings_model(
        guild_id=123456, user_id=987654, display_name="TestUser", avatar_url="https://example.com/avatar.png"
    )

    await cog.anonymous_preview.callback(cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert "embed" in call_kwargs
    assert call_kwargs["ephemeral"] is True


async def test_anonymous_preview_no_settings(cog, make_interaction, clean_db):
    """Preview auto-creates default settings when none exist."""
    interaction = make_interaction()
    await cog.anonymous_preview.callback(cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert "embed" in call_kwargs
    assert call_kwargs["ephemeral"] is True

    # Verify default settings were created in DB
    result = await AnonymousUserSettings.find_one(
        AnonymousUserSettings.guild_id == 123456, AnonymousUserSettings.user_id == 987654
    )
    assert result is not None
    assert result.display_name == "anonymous"
    assert result.avatar_url == ""


async def test_anonymous_preview_guild_none(cog, make_interaction, clean_db):
    """Preview command returns early when guild is None — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_preview.callback(cog, interaction)

    interaction.response.send_message.assert_not_called()


# ========================================
# User Command Tests: send
# ========================================


async def test_anonymous_send_happy_path(cog, make_interaction, make_webhook, clean_db):
    """Full happy path: feature enabled, channel registered, webhook sends message."""
    interaction = make_interaction()
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await cog.repo.set_user_settings_model(guild_id=123456, user_id=987654, display_name="TestUser")
    # Create webhook info in DB so get_webhook can find it
    await AnonymousWebhookInfo(
        guild_id=123456, channel_id=111111, webhook_id=123, webhook_token="test_token"
    ).insert()

    mock_webhook = make_webhook()
    with pytest.MonkeyPatch.context() as m:
        m.setattr("discord.Webhook.partial", classmethod(lambda cls, id, token, client: mock_webhook))
        await cog.anonymous_send.callback(cog, interaction, message="Hello")

    interaction.response.defer.assert_called_once_with(ephemeral=True)
    mock_webhook.send.assert_called_once()
    send_kwargs = mock_webhook.send.call_args.kwargs
    assert send_kwargs["content"] == "Hello"
    assert send_kwargs["username"] == "TestUser"
    interaction.followup.send.assert_called_once()


async def test_anonymous_send_feature_disabled(cog, make_interaction, clean_db):
    """Send with no base_settings in DB — feature not enabled, returns early."""
    interaction = make_interaction()

    await cog.anonymous_send.callback(cog, interaction, message="Hello")

    interaction.response.defer.assert_called_once_with(ephemeral=True)
    interaction.followup.send.assert_called_once()
    # No webhook created since feature is not enabled
    interaction.channel.create_webhook.assert_not_called()


async def test_anonymous_send_user_blocked(cog, make_interaction, make_webhook, clean_db):
    """Blocked user gets you_are_blocked error message."""
    interaction = make_interaction()
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await cog.repo.block_user(guild_id=123456, user_id=987654)
    await cog.repo.set_user_settings_model(guild_id=123456, user_id=987654, display_name="TestUser")

    await cog.anonymous_send.callback(cog, interaction, message="Hello")

    # Blocked user should get error message, no webhook send
    interaction.followup.send.assert_called_once()


async def test_anonymous_send_channel_not_registered(cog, make_interaction, clean_db):
    """Send in a channel with no webhook info — returns early with webhook_error."""
    interaction = make_interaction()
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)

    await cog.anonymous_send.callback(cog, interaction, message="Hello")

    interaction.response.defer.assert_called_once_with(ephemeral=True)
    interaction.followup.send.assert_called_once()
    interaction.channel.create_webhook.assert_not_called()


async def test_anonymous_send_webhook_exception(cog, make_interaction, make_webhook, clean_db):
    """Webhook.send raises — error message sent via followup."""
    interaction = make_interaction()
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await cog.repo.set_user_settings_model(guild_id=123456, user_id=987654, display_name="TestUser")
    # Create webhook info in DB
    await AnonymousWebhookInfo(
        guild_id=123456, channel_id=111111, webhook_id=123, webhook_token="test_token"
    ).insert()

    mock_webhook = make_webhook()
    mock_webhook.send = AsyncMock(side_effect=discord.DiscordException("webhook failed"))

    with pytest.MonkeyPatch.context() as m:
        m.setattr("discord.Webhook.partial", classmethod(lambda cls, id, token, client: mock_webhook))
        await cog.anonymous_send.callback(cog, interaction, message="Hello")

    # Error message sent via followup, then message_sent
    assert interaction.followup.send.call_count == 2


async def test_anonymous_send_no_user_settings(cog, make_interaction, make_webhook, clean_db):
    """Send with no user settings — defaults to display_name='anonymous'."""
    interaction = make_interaction()
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    # Create webhook info in DB so get_webhook can find it
    await AnonymousWebhookInfo(
        guild_id=123456, channel_id=111111, webhook_id=123, webhook_token="test_token"
    ).insert()

    mock_webhook = make_webhook()
    with pytest.MonkeyPatch.context() as m:
        m.setattr("discord.Webhook.partial", classmethod(lambda cls, id, token, client: mock_webhook))
        await cog.anonymous_send.callback(cog, interaction, message="Hello")

    mock_webhook.send.assert_called_once()
    send_kwargs = mock_webhook.send.call_args.kwargs
    assert send_kwargs["username"] == "anonymous"
    interaction.followup.send.assert_called_once()


async def test_anonymous_send_guild_none(cog, make_interaction, clean_db):
    """Send command returns early when guild is None — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_send.callback(cog, interaction, message="Hello")

    interaction.response.defer.assert_not_called()
    interaction.followup.send.assert_not_called()


async def test_anonymous_send_not_text_channel(cog, make_interaction, clean_db):
    """Send command returns early when channel is not TextChannel — no response sent."""
    interaction = make_interaction()
    interaction.channel = AsyncMock(spec=discord.VoiceChannel)
    interaction.channel.id = 111111

    await cog.anonymous_send.callback(cog, interaction, message="Hello")

    interaction.response.defer.assert_not_called()


# ========================================
# Admin Command Tests
# ========================================


async def test_anonymous_enable(cog, make_interaction, clean_db):
    """Enable anonymous feature and verify DB state."""
    interaction = make_interaction()
    await cog.anonymous_enable.callback(cog, interaction)
    interaction.response.send_message.assert_called_once()
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is not None
    assert result.enabled is True


async def test_anonymous_enable_guild_none(cog, make_interaction, clean_db):
    """Enable with guild=None returns early — no response sent, no DB write."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_enable.callback(cog, interaction)

    interaction.response.send_message.assert_not_called()
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is None


async def test_anonymous_disable(cog, make_interaction, clean_db):
    """Disable anonymous feature and verify DB state."""
    interaction = make_interaction()
    await cog.anonymous_disable.callback(cog, interaction)
    interaction.response.send_message.assert_called_once()
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is not None
    assert result.enabled is False


async def test_anonymous_disable_guild_none(cog, make_interaction, clean_db):
    """Disable with guild=None returns early — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_disable.callback(cog, interaction)

    interaction.response.send_message.assert_not_called()


async def test_anonymous_cooldown(cog, make_interaction, clean_db):
    """Set cooldown and verify DB state."""
    interaction = make_interaction()
    await cog.anonymous_cooldown.callback(cog, interaction, seconds=60)
    interaction.response.send_message.assert_called_once()
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is not None
    assert result.cooldown_seconds == 60


async def test_anonymous_cooldown_guild_none(cog, make_interaction, clean_db):
    """Cooldown with guild=None returns early — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_cooldown.callback(cog, interaction, seconds=60)

    interaction.response.send_message.assert_not_called()


async def test_anonymous_block(cog, make_interaction, make_member, clean_db):
    """Block a user and verify DB state."""
    interaction = make_interaction()
    member = make_member(555)
    # Create base settings first so block_user has a document to update
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await cog.anonymous_block.callback(cog, interaction, member=member)
    interaction.response.send_message.assert_called_once()
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is not None
    assert 555 in result.blocked_users


async def test_anonymous_block_guild_none(cog, make_interaction, make_member, clean_db):
    """Block with guild=None returns early — no response sent."""
    interaction = make_interaction()
    interaction.guild = None
    member = make_member(555)

    await cog.anonymous_block.callback(cog, interaction, member=member)

    interaction.response.send_message.assert_not_called()


async def test_anonymous_unblock(cog, make_interaction, make_member, clean_db):
    """Unblock a previously blocked user and verify DB state."""
    interaction = make_interaction()
    member = make_member(555)
    # Block first, then unblock
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await cog.repo.block_user(guild_id=123456, user_id=555)
    await cog.anonymous_unblock.callback(cog, interaction, member=member)
    interaction.response.send_message.assert_called_once()
    result = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == 123456)
    assert result is not None
    assert 555 not in result.blocked_users


async def test_anonymous_unblock_not_blocked(cog, make_interaction, make_member, clean_db):
    """Unblock a user who was never blocked — should still call send_message (idempotent)."""
    interaction = make_interaction()
    member = make_member(555)
    # Create base settings but don't block the user
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await cog.anonymous_unblock.callback(cog, interaction, member=member)
    interaction.response.send_message.assert_called_once()


async def test_anonymous_config(cog, make_interaction, clean_db):
    """Config command sends an embed with current settings."""
    interaction = make_interaction()
    # Enable feature and add a webhook info to have non-empty config
    await cog.repo.set_base_settings_model(guild_id=123456, enabled=True)
    await AnonymousWebhookInfo(
        guild_id=123456, channel_id=111111, webhook_id=123, webhook_token="test_token"
    ).insert()
    await cog.anonymous_config.callback(cog, interaction)
    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert "embed" in call_kwargs
    assert isinstance(call_kwargs["embed"], discord.Embed)


async def test_anonymous_config_no_settings(cog, make_interaction, clean_db):
    """Config with no prior settings auto-creates defaults and sends embed."""
    interaction = make_interaction()
    await cog.anonymous_config.callback(cog, interaction)
    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    assert "embed" in call_kwargs
    assert isinstance(call_kwargs["embed"], discord.Embed)


async def test_anonymous_config_guild_none(cog, make_interaction, clean_db):
    """Config with guild=None returns early — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_config.callback(cog, interaction)

    interaction.response.send_message.assert_not_called()


# ========================================
# add_channel tests
# ========================================


async def test_anonymous_add_channel(cog, make_interaction, make_channel, clean_db):
    """add_channel adds channel to DB and sends confirmation message."""
    interaction = make_interaction()
    channel = make_channel()
    await cog.anonymous_add_channel.callback(cog, interaction, channel=channel)
    interaction.response.send_message.assert_called_once()
    # Verify DB has the webhook info
    result = await AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == 111111)
    assert result is not None


async def test_anonymous_add_channel_guild_none(cog, make_interaction, make_channel, clean_db):
    """add_channel with guild=None returns early — no response sent."""
    interaction = make_interaction()
    interaction.guild = None
    channel = make_channel()

    await cog.anonymous_add_channel.callback(cog, interaction, channel=channel)

    interaction.response.send_message.assert_not_called()


async def test_anonymous_add_channel_already_exists(cog, make_interaction, make_channel, make_webhook, clean_db):
    """add_channel is idempotent — adding same channel twice returns already_exists message."""
    interaction = make_interaction()
    channel = make_channel()
    # First add
    await cog.anonymous_add_channel.callback(cog, interaction, channel=channel)
    # Second add — get_webhook finds existing record, returns already_exists
    mock_webhook = make_webhook()
    with pytest.MonkeyPatch.context() as m:
        m.setattr("discord.Webhook.partial", classmethod(lambda cls, id, token, client: mock_webhook))
        await cog.anonymous_add_channel.callback(cog, interaction, channel=channel)
    assert interaction.response.send_message.call_count == 2


async def test_anonymous_add_channel_multiple_channels(cog, make_interaction, make_channel, clean_db):
    """add_channel can add multiple different channels to the same guild."""
    interaction = make_interaction()
    channel_a = make_channel(channel_id=111111)
    channel_b = make_channel(channel_id=222222)
    await cog.anonymous_add_channel.callback(cog, interaction, channel=channel_a)
    await cog.anonymous_add_channel.callback(cog, interaction, channel=channel_b)
    result_a = await AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == 111111)
    result_b = await AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == 222222)
    assert result_a is not None
    assert result_b is not None


# ========================================
# del_channel tests
# ========================================


async def test_anonymous_del_channel(cog, make_interaction, clean_db):
    """del_channel removes channel from DB and sends confirmation message."""
    interaction = make_interaction()
    # First add a webhook info for the channel
    await AnonymousWebhookInfo(
        guild_id=123456, channel_id=111111, webhook_id=123, webhook_token="test_token"
    ).insert()
    # Mock channel.webhooks to return the matching webhook for cleanup
    mock_webhook = AsyncMock(spec=discord.Webhook)
    mock_webhook.id = 123
    mock_webhook.delete = AsyncMock()
    interaction.channel.webhooks = AsyncMock(return_value=[mock_webhook])
    # Now delete it
    await cog.anonymous_del_channel.callback(cog, interaction, channel=interaction.channel)
    interaction.response.send_message.assert_called_once()
    # Verify DB no longer has the webhook info
    result = await AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == 111111)
    assert result is None


async def test_anonymous_del_channel_guild_none(cog, make_interaction, clean_db):
    """del_channel with guild=None returns early — no response sent."""
    interaction = make_interaction()
    interaction.guild = None

    await cog.anonymous_del_channel.callback(cog, interaction, channel=interaction.channel)

    interaction.response.send_message.assert_not_called()


async def test_anonymous_del_channel_nonexistent(cog, make_interaction, clean_db):
    """del_channel on a channel not in DB still sends message (graceful no-op)."""
    interaction = make_interaction()
    # No channel added — del_channel on nonexistent entry
    await cog.anonymous_del_channel.callback(cog, interaction, channel=interaction.channel)
    interaction.response.send_message.assert_called_once()
