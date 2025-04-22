from isekaitavern.services.repository import RedisClient

from .model import TVModel


class WelcomeFarewell:
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client

    async def set_model(
        self,
        model_cls: type[TVModel],
        guild_id: int,
        set_by_member_id: int | None = None,
        channel_id: int | None = None,
        title: str | None = None,
        msg: str | None = None,
    ) -> None:
        model = await self.require_model(model_cls, guild_id)
        model.set_by_member_id = set_by_member_id or model.set_by_member_id
        model.channel_id = channel_id or model.channel_id
        model.title = title or model.title
        model.description = msg or model.description
        await model.save()

    async def get_model(
        self,
        model_cls: type[TVModel],
        guild_id: int,
    ) -> TVModel | None:
        return await model_cls.find_one(model_cls.guild_id == guild_id)

    async def require_model(self, model_cls: type[TVModel], guild_id: int) -> TVModel:
        model = await self.get_model(model_cls, guild_id)
        if not model:
            model = model_cls(guild_id=guild_id)
        return model
