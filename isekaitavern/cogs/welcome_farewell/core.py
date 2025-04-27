import beanie.operators as ops

from isekaitavern.utils.helpers import ensure_awaitable

from .model import WelcomeFarewellModel_T


class WelcomeFarewell:
    async def set_welcome_farewell_model(
        self,
        model_cls: type[WelcomeFarewellModel_T],
        guild_id: int,
        *,
        set_by_member_id: int | None = None,
        channel_id: int | None = None,
        title: str | None = None,
        msg: str | None = None,
        color: int | None = None,
        thumbnail_url: str | None = None,
        image_url: str | None = None,
        enabled: bool | None = None,
    ) -> WelcomeFarewellModel_T:
        params = {
            "set_by_member_id": set_by_member_id,
            "channel_id": channel_id,
            "title": title,
            "description": msg,
            "color": color,
            "thumbnail_url": thumbnail_url,
            "image_url": image_url,
            "enabled": enabled,
        }

        params = {k: v for k, v in params.items() if v is not None}

        return await ensure_awaitable(
            model_cls.find_one(model_cls.guild_id == guild_id).upsert(
                ops.Set(params),
                on_insert=model_cls(guild_id=guild_id, **params),
            ),
        )

    async def get_welcome_farewell_model(
        self,
        model_cls: type[WelcomeFarewellModel_T],
        guild_id: int,
    ) -> WelcomeFarewellModel_T | None:
        return await model_cls.find_one(model_cls.guild_id == guild_id)
