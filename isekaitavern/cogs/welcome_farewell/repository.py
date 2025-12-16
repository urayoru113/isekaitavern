from collections.abc import Awaitable
from typing import cast

import beanie.odm.operators.update.general as ops

from .model import WelcomeFarewellModelT


class WelcomeFarewellRepository:
    async def get_model(self, model_cls: type[WelcomeFarewellModelT], guild_id: int) -> WelcomeFarewellModelT | None:
        return await model_cls.find_one(model_cls.guild_id == guild_id)

    async def set_model(
        self,
        model_cls: type[WelcomeFarewellModelT],
        guild_id: int,
        *,
        channel_id: int | None = None,
        title: str | None = None,
        description: str | None = None,
        color: int | None = None,
        thumbnail_url: str | None = None,
        image_url: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        update_data = {
            "channel_id": channel_id,
            "title": title,
            "description": description,
            "color": color,
            "thumbnail_url": thumbnail_url,
            "image_url": image_url,
            "enabled": enabled,
        }

        update_data = {k: v for k, v in update_data.items() if v is not None}
        await cast(
            Awaitable,
            model_cls.find_one(model_cls.guild_id == guild_id).upsert(
                ops.Set(update_data), on_insert=model_cls(guild_id=guild_id, **update_data)
            ),
        )
