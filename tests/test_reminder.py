import datetime
from unittest.mock import AsyncMock, Mock

import discord
import pytest
from dateutil.relativedelta import relativedelta

from isekaitavern.cogs.reminder.model import ReminderGuildRecord, ReminderRecurrence, ReminderUserRecord
from isekaitavern.errno import PastTimeError


def _future_time(minutes=5):
    return datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=minutes)


# ========================================
# Section 1: Smoke Tests
# ========================================


async def test_smoke_reminder_cog_instantiation(reminder_cog):
    """Verify reminder_cog fixture creates ReminderCog with real repo and service."""
    assert reminder_cog.repo is not None
    assert reminder_cog.service is not None


async def test_smoke_interaction_mock(make_interaction):
    """Verify make_interaction creates valid interaction mock."""
    interaction = make_interaction()
    assert interaction.guild.id == 123456
    assert interaction.user.id == 987654
    assert interaction.channel.id == 111111
    assert callable(interaction.response.send_message)
    assert callable(interaction.response.defer)
    assert callable(interaction.followup.send)


# ========================================
# Section 2: User Reminder Tests (DM context)
# ========================================


async def test_user_reminder_create(reminder_cog, clean_db):
    """Create a user reminder via service and verify DB record."""
    remind_time = _future_time(minutes=10)
    record = await reminder_cog.service.add_user_reminder(
        user_id=987654, message="Test reminder", remind_time=remind_time
    )
    assert record is not None
    assert record.user_id == 987654
    assert record.message == "Test reminder"

    result = await ReminderUserRecord.find_one(ReminderUserRecord.user_id == 987654)
    assert result is not None
    assert result.message == "Test reminder"


async def test_user_reminder_create_duplicate(reminder_cog, clean_db):
    """Creating two user reminders with same params results in two DB records."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="Dup", remind_time=remind_time)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="Dup", remind_time=remind_time)

    results = await ReminderUserRecord.find(ReminderUserRecord.user_id == 987654).to_list()
    assert len(results) == 2


async def test_user_reminder_create_past_time(reminder_cog, clean_db):
    """Creating a user reminder with past time raises PastTimeError."""
    past_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
    with pytest.raises(PastTimeError):
        await reminder_cog.service.add_user_reminder(user_id=987654, message="Past", remind_time=past_time)


async def test_user_reminder_list_empty(reminder_cog, make_interaction, clean_db):
    """List command in DM context with no reminders shows user_list_empty embed."""
    interaction = make_interaction()
    interaction.guild_id = None
    interaction.guild = None

    await reminder_cog.list_reminders.callback(reminder_cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.description is not None


async def test_user_reminder_list_with_items(reminder_cog, make_interaction, clean_db):
    """List command in DM context shows user reminders as embed fields."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="First", remind_time=remind_time)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="Second", remind_time=remind_time)

    interaction = make_interaction()
    interaction.guild_id = None
    interaction.guild = None

    await reminder_cog.list_reminders.callback(reminder_cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert len(embed.fields) == 2


async def test_user_reminder_delete(reminder_cog, make_interaction, clean_db):
    """Delete a user reminder via command and verify DB removal."""
    remind_time = _future_time(minutes=10)
    record = await reminder_cog.service.add_user_reminder(user_id=987654, message="Delete me", remind_time=remind_time)

    interaction = make_interaction()
    interaction.guild_id = None
    interaction.guild = None

    await reminder_cog.delete_reminder.callback(reminder_cog, interaction, reminder_id=str(record.id))

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.color == discord.Color.green()

    result = await ReminderUserRecord.get(record.id)
    assert result is None


async def test_user_reminder_delete_not_found(reminder_cog, make_interaction, clean_db):
    """Delete a non-existent reminder shows delete_not_found embed."""
    interaction = make_interaction()
    interaction.guild_id = None
    interaction.guild = None

    await reminder_cog.delete_reminder.callback(reminder_cog, interaction, reminder_id="000000000000000000000000")

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.color == discord.Color.red()


# ========================================
# Section 3: Guild Reminder Tests
# ========================================


async def test_guild_reminder_create(reminder_cog, clean_db):
    """Create a guild reminder via service and verify DB record."""
    remind_time = _future_time(minutes=10)
    record = await reminder_cog.service.add_guild_reminder(
        user_id=987654, message="Guild reminder", remind_time=remind_time, channel_id=111111, guild_id=123456
    )
    assert record is not None
    assert record.channel_id == 111111
    assert record.guild_id == 123456

    result = await ReminderGuildRecord.find_one(ReminderGuildRecord.channel_id == 111111)
    assert result is not None
    assert result.message == "Guild reminder"


async def test_guild_reminder_create_duplicate(reminder_cog, clean_db):
    """Creating two guild reminders with same params results in two DB records."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.service.add_guild_reminder(
        user_id=987654, message="Dup", remind_time=remind_time, channel_id=111111, guild_id=123456
    )
    await reminder_cog.service.add_guild_reminder(
        user_id=987654, message="Dup", remind_time=remind_time, channel_id=111111, guild_id=123456
    )

    results = await ReminderGuildRecord.find(ReminderGuildRecord.channel_id == 111111).to_list()
    assert len(results) == 2


async def test_guild_reminder_list(reminder_cog, make_interaction, clean_db):
    """List command in guild context shows channel reminders as embed fields."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.service.add_guild_reminder(
        user_id=987654, message="First", remind_time=remind_time, channel_id=111111, guild_id=123456
    )
    await reminder_cog.service.add_guild_reminder(
        user_id=987654, message="Second", remind_time=remind_time, channel_id=111111, guild_id=123456
    )

    interaction = make_interaction()
    await reminder_cog.list_reminders.callback(reminder_cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert len(embed.fields) == 2
    assert embed.title is not None


async def test_guild_reminder_list_empty(reminder_cog, make_interaction, clean_db):
    """List command in guild context with no reminders shows channel_list_empty embed."""
    interaction = make_interaction()
    await reminder_cog.list_reminders.callback(reminder_cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.description is not None


async def test_guild_reminder_delete(reminder_cog, make_interaction, clean_db):
    """Delete a guild reminder via command and verify DB removal."""
    remind_time = _future_time(minutes=10)
    record = await reminder_cog.service.add_guild_reminder(
        user_id=987654, message="Delete me", remind_time=remind_time, channel_id=111111, guild_id=123456
    )

    interaction = make_interaction()
    await reminder_cog.delete_reminder.callback(reminder_cog, interaction, reminder_id=str(record.id))

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.color == discord.Color.green()

    result = await ReminderGuildRecord.get(record.id)
    assert result is None


# ========================================
# Section 4: Permission Tests
# ========================================


async def test_set_reminder_no_permission(reminder_cog, make_interaction, clean_db):
    """Set reminder without manage_guild permission returns no_permission embed."""
    interaction = make_interaction()
    interaction.channel.permissions_for = Mock(return_value=discord.Permissions(manage_guild=False))

    await reminder_cog.set_reminder.callback(reminder_cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.color == discord.Color.red()


async def test_delete_reminder_no_permission(reminder_cog, make_interaction, clean_db):
    """Delete reminder without manage_guild permission returns no_permission embed."""
    interaction = make_interaction()
    interaction.channel.permissions_for = Mock(return_value=discord.Permissions(manage_guild=False))

    await reminder_cog.delete_reminder.callback(reminder_cog, interaction, reminder_id="000000000000000000000000")

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.color == discord.Color.red()


async def test_set_reminder_invalid_state(reminder_cog, make_interaction, clean_db):
    """Set reminder with channel=None in guild context returns invalid_state embed."""
    interaction = make_interaction()
    interaction.channel = None

    await reminder_cog.set_reminder.callback(reminder_cog, interaction)

    interaction.response.send_message.assert_called_once()
    call_kwargs = interaction.response.send_message.call_args.kwargs
    embed = call_kwargs["embed"]
    assert embed.color == discord.Color.red()


# ========================================
# Section 5: Service Tests
# ========================================


async def test_calculate_next_time_daily(reminder_cog):
    """DAILY recurrence adds 1 day to current time."""
    now = datetime.datetime.now(datetime.UTC)
    result = reminder_cog.service.calculate_next_time(now, ReminderRecurrence.DAILY)
    assert result == now + datetime.timedelta(days=1)


async def test_calculate_next_time_weekly(reminder_cog):
    """WEEKLY recurrence adds 1 week to current time."""
    now = datetime.datetime.now(datetime.UTC)
    result = reminder_cog.service.calculate_next_time(now, ReminderRecurrence.WEEKLY)
    assert result == now + datetime.timedelta(weeks=1)


async def test_calculate_next_time_monthly(reminder_cog):
    """MONTHLY recurrence adds 1 month to current time."""
    now = datetime.datetime.now(datetime.UTC)
    result = reminder_cog.service.calculate_next_time(now, ReminderRecurrence.MONTHLY)
    assert result == now + relativedelta(months=1)


async def test_calculate_next_time_yearly(reminder_cog):
    """YEARLY recurrence adds 1 year to current time."""
    now = datetime.datetime.now(datetime.UTC)
    result = reminder_cog.service.calculate_next_time(now, ReminderRecurrence.YEARLY)
    assert result == now + relativedelta(years=1)


async def test_process_due_reminders_once_deletes(reminder_cog, clean_db):
    """ONCE reminder is deleted from DB after processing."""
    past_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
    record = await ReminderUserRecord(
        user_id=987654, message="Past reminder", remind_time=past_time, recurrence=ReminderRecurrence.ONCE
    ).insert()
    record_id = record.id

    mock_user = AsyncMock()
    mock_user.send = AsyncMock()
    reminder_cog.bot.get_user = Mock(return_value=mock_user)

    await reminder_cog.service.process_due_reminders()

    mock_user.send.assert_called_once_with("Past reminder")
    result = await ReminderUserRecord.get(record_id)
    assert result is None


async def test_process_due_reminders_recurring_updates(reminder_cog, clean_db):
    """Recurring reminder is updated in DB with next time after processing."""
    past_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
    record = await ReminderUserRecord(
        user_id=987654, message="Recurring reminder", remind_time=past_time, recurrence=ReminderRecurrence.DAILY
    ).insert()
    record_id = record.id

    mock_user = AsyncMock()
    mock_user.send = AsyncMock()
    reminder_cog.bot.get_user = Mock(return_value=mock_user)

    await reminder_cog.service.process_due_reminders()

    mock_user.send.assert_called_once_with("Recurring reminder")
    result = await ReminderUserRecord.get(record_id)
    assert result is not None
    assert result.remind_time.replace(tzinfo=datetime.UTC) > past_time


# ========================================
# Section 6: Repository Tests
# ========================================


async def test_repo_get_user_reminders(reminder_cog, clean_db):
    """get_user_reminders returns all reminders for a user."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.repo.create_user_reminder(user_id=987654, message="A", remind_time=remind_time)
    await reminder_cog.repo.create_user_reminder(user_id=987654, message="B", remind_time=remind_time)
    await reminder_cog.repo.create_user_reminder(user_id=987654, message="C", remind_time=remind_time)

    results = await reminder_cog.repo.get_user_reminders(987654)
    assert len(results) == 3


async def test_repo_get_channel_reminders(reminder_cog, clean_db):
    """get_channel_reminders returns all reminders for a channel."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.repo.create_guild_reminder(
        user_id=987654, message="A", remind_time=remind_time, channel_id=111111, guild_id=123456
    )
    await reminder_cog.repo.create_guild_reminder(
        user_id=987654, message="B", remind_time=remind_time, channel_id=111111, guild_id=123456
    )

    results = await reminder_cog.repo.get_channel_reminders(111111)
    assert len(results) == 2


async def test_repo_get_guild_reminders(reminder_cog, clean_db):
    """get_guild_reminders returns all reminders for a guild."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.repo.create_guild_reminder(
        user_id=987654, message="A", remind_time=remind_time, channel_id=111111, guild_id=123456
    )

    results = await reminder_cog.repo.get_guild_reminders(123456)
    assert len(results) == 1
    assert results[0].guild_id == 123456


async def test_repo_get_due_reminders(reminder_cog, clean_db):
    """get_due_reminders returns only past-due reminders."""
    past_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
    future_time = _future_time(minutes=60)

    await reminder_cog.repo.create_user_reminder(user_id=987654, message="Past", remind_time=past_time)
    await reminder_cog.repo.create_user_reminder(user_id=987654, message="Future", remind_time=future_time)

    now = datetime.datetime.now(datetime.UTC)
    results = await reminder_cog.repo.get_due_reminders(now)
    messages = [r.message for r in results]
    assert "Past" in messages
    assert "Future" not in messages


async def test_repo_delete_reminder(reminder_cog, clean_db):
    """delete_reminder removes a reminder and returns True."""
    remind_time = _future_time(minutes=10)
    record = await reminder_cog.repo.create_user_reminder(user_id=987654, message="To delete", remind_time=remind_time)

    result = await reminder_cog.repo.delete_reminder(str(record.id))
    assert result is True

    db_result = await ReminderUserRecord.get(record.id)
    assert db_result is None


async def test_repo_delete_reminder_not_found(reminder_cog, clean_db):
    """delete_reminder returns False for non-existent reminder."""
    result = await reminder_cog.repo.delete_reminder("000000000000000000000000")
    assert result is False


# ========================================
# Section 7: Autocomplete
# ========================================


async def test_reminder_id_autocomplete(reminder_cog, make_interaction, clean_db):
    """Autocomplete returns all reminders for the user in DM context."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="Hello", remind_time=remind_time)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="World", remind_time=remind_time)

    interaction = make_interaction()
    interaction.guild_id = None
    interaction.guild = None

    choices = await reminder_cog.reminder_id_autocomplete(interaction, current="")
    assert len(choices) == 2


async def test_reminder_id_autocomplete_filters(reminder_cog, make_interaction, clean_db):
    """Autocomplete filters reminders by current query string."""
    remind_time = _future_time(minutes=10)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="Hello", remind_time=remind_time)
    await reminder_cog.service.add_user_reminder(user_id=987654, message="World", remind_time=remind_time)

    interaction = make_interaction()
    interaction.guild_id = None
    interaction.guild = None

    choices = await reminder_cog.reminder_id_autocomplete(interaction, current="hel")
    assert len(choices) == 1
    assert "Hello" in choices[0].name
