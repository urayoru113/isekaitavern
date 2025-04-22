import typing
from collections import defaultdict

import redis.asyncio as redis
from redis.typing import FieldT, ResponseT

from isekaitavern.utils.redis import validate_async

TVGuildSettings = typing.TypeVar("TVGuildSettings", bound="GuildSettingsObj")


class GuildSettingsObj(typing.Protocol):
    guild_id: int

    def __init__(self, *args, **kwargs):
        pass


class RedisClient:
    expire_times: dict[str, int]

    def __init__(self, redis: redis.Redis, default_exprie_time: int = 3600) -> None:
        self.__redis = redis
        self.expire_times = defaultdict(lambda: default_exprie_time)

    async def get(self, key: str) -> ResponseT:
        await self.redis.expire(key, self.expire_times[key])
        return await self.redis.get(key)

    async def set(self, key: str, value: FieldT, *, expired_time: int | None = None) -> None:
        if expired_time:
            self.expire_times[key] = expired_time
        await self.redis.set(key, value, ex=self.expire_times[key])

    async def lpush(self, key: str, *value: FieldT, expired_time: int | None = None) -> None:
        if expired_time:
            self.expire_times[key] = expired_time
        await validate_async(self.redis.lpush(key, *value))
        await self.redis.expire(key, self.expire_times[key])

    async def rpush(self, key: str, *value: FieldT, expired_time: int | None = None) -> None:
        if expired_time:
            self.expire_times[key] = expired_time
        await validate_async(self.redis.rpush(key, *value))
        await self.redis.expire(key, self.expire_times[key])

    async def lpop(self, key: str) -> str:
        value = await validate_async(self.redis.lpop(key))
        assert isinstance(value, str), f"Expected str, got {type(value), value}"
        await self.redis.expire(key, self.expire_times[key])
        return value

    async def rpop(self, key: str) -> str:
        value = await validate_async(self.redis.rpop(key))
        assert isinstance(value, str), f"Expected str, got {type(value), value}"
        await self.redis.expire(key, self.expire_times[key])
        return value

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        value = await validate_async(self.redis.lrange(key, start, end))
        await self.redis.expire(key, self.expire_times[key])
        return value

    async def llen(self, key: str) -> int:
        value = await validate_async(self.redis.llen(key))
        await self.redis.expire(key, self.expire_times[key])
        return value

    @property
    def redis(self) -> redis.Redis:
        return self.__redis
