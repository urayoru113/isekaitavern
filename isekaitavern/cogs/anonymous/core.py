import beanie.operators as ops

from isekaitavern.utils.helpers import ensure_awaitable

from .model import AnonymousMemberModel, AnonymousSettingsModel


class Anonymous:
    async def set_anonymous_settings(
        self,
        guild_id: int,
        enable: bool,
    ) -> AnonymousSettingsModel:
        update_operations = ops.Set({AnonymousSettingsModel.enabled: enable})

        return await ensure_awaitable(
            AnonymousSettingsModel.find_one(
                AnonymousSettingsModel.guild_id == guild_id,
            ).upsert(
                update_operations,
                on_insert=AnonymousSettingsModel(guild_id=guild_id, enabled=enable),
            ),
        )

    async def add_anonymous_channel(self, guild_id: int, channel_id: int) -> AnonymousSettingsModel:
        update_operations = ops.AddToSet({AnonymousSettingsModel.channel_ids: channel_id})  # type: ignore
        return await ensure_awaitable(
            AnonymousSettingsModel.find_one(
                AnonymousSettingsModel.guild_id == guild_id,
            ).upsert(
                update_operations,
                on_insert=AnonymousSettingsModel(guild_id=guild_id, channel_ids={channel_id}),
            ),
        )

    async def remove_anonymous_channel(self, guild_id: int, channel_id: int) -> AnonymousSettingsModel:
        update_operations = ops.Pull({AnonymousSettingsModel.channel_ids: channel_id})  # # type: ignore
        return await ensure_awaitable(
            AnonymousSettingsModel.find_one(
                AnonymousSettingsModel.guild_id == guild_id,
            ).upsert(
                update_operations,
                on_insert=AnonymousSettingsModel(guild_id=guild_id),
            ),
        )

    async def set_anonymous_member(
        self,
        guild_id: int,
        member_id: int,
        nickname: str,
        avatar_url: str | None = None,
    ) -> AnonymousMemberModel:
        update_operations = ops.Set(
            {
                AnonymousMemberModel.nickname: nickname,
                AnonymousMemberModel.avatar_url: avatar_url,
            },
        )
        return await ensure_awaitable(
            AnonymousMemberModel.find_one(
                AnonymousMemberModel.guild_id == guild_id,
                AnonymousMemberModel.member_id == member_id,
            ).upsert(
                update_operations,
                on_insert=AnonymousMemberModel(
                    guild_id=guild_id,
                    member_id=member_id,
                    nickname=nickname,
                    avatar_url=avatar_url,
                ),
            ),
        )
