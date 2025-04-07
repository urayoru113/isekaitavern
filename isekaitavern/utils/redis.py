import redis.asyncio as redis


class RedisManager:
    __redis: redis.Redis | None = None

    def __init__(self, url: str):
        self.url = url

    def connect(self):
        self.__redis = redis.Redis.from_url(self.url)

    @property
    def redis(self):
        if self.__redis is None:
            self.connect()
        return self.__redis

    async def set(self, key: str, value: str):
        await self.redis.set(key, value)

    async def get(self, key: str):
        return await self.redis.get(key)
