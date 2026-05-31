import datetime
import typing

import beanie.odm.operators.update.array as array_ops
import beanie.odm.operators.update.general as ops
import redis.asyncio as redis

from ...types import SupportsStr
from ...utils.helpers import ensure_awaitable
from .model import AnonymousBaseSettings, AnonymousUserSettings, AnonymousWebhookInfo


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

    async def check_and_set_cooldown(self, guild_id: int, user_id: int, cooldown_seconds: int) -> int | None:
        """Check cooldown for an anonymous sender and set it if allowed.

        Returns:
            Remaining seconds if still on cooldown.
            None if cooldown is not active (and the cooldown is set).
        """

        key = self._make_key("cooldown", guild_id, user_id)
        ttl = await ensure_awaitable(self.redis.ttl(key))
        # redis returns:
        # -1: key exists but has no expiry
        # -2: key does not exist
        if ttl is not None and ttl > 0:
            return int(ttl)

        await ensure_awaitable(self.redis.set(key, "1", ex=cooldown_seconds))
        return None

    async def get_webhook_info(self, channel_id: int) -> AnonymousWebhookInfo | None:
        key = self._make_key("webhook", channel_id)
        raw_json = await ensure_awaitable(self.redis.get(name=key))
        if not raw_json:
            anonymous_webhook_auth = await AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == channel_id)
            if not anonymous_webhook_auth:
                return None
            await ensure_awaitable(self.redis.set(key, anonymous_webhook_auth.model_dump_json(), ex=3600))
        else:
            anonymous_webhook_auth = AnonymousWebhookInfo.model_validate_json(raw_json)
        return anonymous_webhook_auth

    async def get_all_webhook_infos(self, guild_id: int) -> list[AnonymousWebhookInfo]:
        webhook_infos = await AnonymousWebhookInfo.find(AnonymousWebhookInfo.guild_id == guild_id).to_list(None)
        return webhook_infos

    async def add_webhook_info(self, guild_id: int, channel_id: int, webhook_id: int, webhook_token: str) -> None:
        now = datetime.datetime.now(datetime.UTC)
        await ensure_awaitable(
            AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == channel_id).upsert(
                ops.Set({"webhook_id": webhook_id, "webhook_token": webhook_token, "updated_at": now}),
                on_insert=AnonymousWebhookInfo(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    webhook_id=webhook_id,
                    webhook_token=webhook_token,
                    updated_at=now,
                ),
            ),
        )

    async def remove_webhook_info(self, channel_id: int) -> None:
        key = self._make_key("webhook", channel_id)
        await ensure_awaitable(self.redis.delete(key))
        await ensure_awaitable(AnonymousWebhookInfo.find_one(AnonymousWebhookInfo.channel_id == channel_id).delete())

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
