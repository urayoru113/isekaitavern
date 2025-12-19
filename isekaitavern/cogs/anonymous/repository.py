import typing

import beanie.odm.operators.update.array as array_ops
import beanie.odm.operators.update.general as ops
import redis.asyncio as redis

from ...types import SupportsStr
from ...utils.helpers import ensure_awaitable
from .model import AnonymousBaseSettings, AnonymousUserSettings


class AnonymousRepository:
    """Data access layer for anonymous feature"""

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def get_base_settings_model(self, guild_id: int) -> AnonymousBaseSettings | None:
        key = self._make_base_settings_key(guild_id)

        raw_json = await ensure_awaitable(self.redis.get(key))

        if not raw_json:
            base_settings_model = await AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == guild_id)
            if not base_settings_model:
                return None

            await ensure_awaitable(self.redis.set(key, base_settings_model.model_dump_json()))
        else:
            base_settings_model = AnonymousBaseSettings.model_validate_json(raw_json)

        return base_settings_model

    async def set_base_settings_model(
        self,
        guild_id: int,
        *,
        enabled: bool | None = None,
        channel_ids: set[int] | None = None,
        cooldown_seconds: int | None = None,
        blocked_users: set[int] | None = None,
    ) -> None:
        update_data = {
            "enabled": enabled,
            "channel_ids": channel_ids,
            "cooldown_seconds": cooldown_seconds,
            "blocked_users": blocked_users,
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}

        await ensure_awaitable(
            AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == guild_id).upsert(
                ops.Set(update_data), on_insert=AnonymousBaseSettings(guild_id=guild_id, **update_data)
            ),
        )

        await ensure_awaitable(self.redis.delete(self._make_base_settings_key(guild_id)))

    async def add_channel(self, guild_id: int, channel_id: int) -> None:
        """Add a channel to anonymous channel list atomically"""
        await ensure_awaitable(
            AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == guild_id).upsert(
                array_ops.AddToSet({"channel_ids": channel_id}),
                on_insert=AnonymousBaseSettings(guild_id=guild_id, channel_ids={channel_id}),
            ),
        )
        await ensure_awaitable(self.redis.delete(self._make_base_settings_key(guild_id)))

    async def remove_channel(self, guild_id: int, channel_id: int) -> None:
        """Remove a channel from anonymous channel list atomically"""
        await ensure_awaitable(
            AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == guild_id).update(
                array_ops.Pull({"channel_ids": channel_id}),
            ),
        )
        await ensure_awaitable(self.redis.delete(self._make_base_settings_key(guild_id)))

    async def block_user(self, guild_id: int, user_id: int) -> None:
        """Block a user from using anonymous feature atomically"""
        await ensure_awaitable(
            AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == guild_id).upsert(
                array_ops.AddToSet({"blocked_users": user_id}),
                on_insert=AnonymousBaseSettings(guild_id=guild_id, blocked_users={user_id}),
            ),
        )
        await ensure_awaitable(self.redis.delete(self._make_base_settings_key(guild_id)))

    async def unblock_user(self, guild_id: int, user_id: int) -> None:
        """Unblock a user from anonymous feature atomically"""
        await ensure_awaitable(
            AnonymousBaseSettings.find_one(AnonymousBaseSettings.guild_id == guild_id).update(
                array_ops.Pull({"blocked_users": user_id})
            ),
        )
        await ensure_awaitable(self.redis.delete(self._make_base_settings_key(guild_id)))

    async def get_user_settings_model(self, guild_id: int, user_id: int) -> AnonymousUserSettings | None:
        key = self._make_user_settings_key(guild_id, user_id)
        raw_json = await ensure_awaitable(self.redis.get(name=key))

        if not raw_json:
            user_settings_model = await AnonymousUserSettings.find_one(
                AnonymousUserSettings.guild_id == guild_id, AnonymousUserSettings.user_id == user_id
            )
            if not user_settings_model:
                return None

            await ensure_awaitable(
                self.redis.set(
                    name=key,
                    value=user_settings_model.model_dump_json(),
                    ex=3600,
                )
            )
        else:
            user_settings_model = AnonymousUserSettings.model_validate_json(raw_json)

        return user_settings_model

    async def set_user_settings_model(
        self,
        guild_id: int,
        user_id: int,
        *,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> None:
        update_data: dict[str, typing.Any] = {
            "display_name": display_name,
            "avatar_url": avatar_url,
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}

        await ensure_awaitable(
            AnonymousUserSettings.find_one(
                AnonymousUserSettings.guild_id == guild_id, AnonymousUserSettings.user_id == user_id
            ).upsert(
                ops.Set(update_data), on_insert=AnonymousUserSettings(guild_id=guild_id, user_id=user_id, **update_data)
            ),
        )

        await ensure_awaitable(self.redis.delete(self._make_user_settings_key(guild_id, user_id)))

    def _make_key(self, *args: SupportsStr) -> str:
        return f"{self.__class__.__name__}:" + ":".join(str(x) for x in args)

    def _make_base_settings_key(self, guild_id: int) -> str:
        return self._make_key("base_settings", guild_id)

    def _make_user_settings_key(self, guild_id: int, user_id: int) -> str:
        return self._make_key("user_settings", guild_id, user_id)
