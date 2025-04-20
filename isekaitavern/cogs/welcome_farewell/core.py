import discord

from isekaitavern.services.repository import RedisClient

from .model import WelcomeFareWellModel


class WelcomeFarewell:
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client

    async def set_welcome_msg(self, guild: discord.Guild, set_by_member: discord.Member, msg: str):
        model = await WelcomeFareWellModel.find_one(WelcomeFareWellModel.guild_id == guild.id)
        if not model:
            model = WelcomeFareWellModel(guild_id=guild.id, welcome_message=msg, set_by_member_id=set_by_member.id)
        model.welcome_message = msg
        await model.save()

    async def set_farewell_msg(self, guild: discord.Guild, set_by_member: discord.Member, msg: str):
        model = await WelcomeFareWellModel.find_one(WelcomeFareWellModel.guild_id == guild.id)
        if not model:
            model = WelcomeFareWellModel(guild_id=guild.id, farewell_message=msg, set_by_member_id=set_by_member.id)
        model.farewell_message = msg
        await model.save()

    async def get_welcome_msg(self, member: discord.Member) -> str | None:
        raw_msg = await self.get_raw_welcome_msg(member)
        return raw_msg.format(member=f"<@{member.id}>") if raw_msg else None

    async def get_farewell_msg(self, member: discord.Member) -> str | None:
        raw_msg = await self.get_raw_farewell_msg(member)
        return raw_msg.format(member=f"<@{member.id}>") if raw_msg else None

    async def get_raw_welcome_msg(self, member: discord.Member) -> str | None:
        model = await WelcomeFareWellModel.find_one(WelcomeFareWellModel.guild_id == member.guild.id)
        if not model:
            return None
        return model.welcome_message

    async def get_raw_farewell_msg(self, member: discord.Member) -> str | None:
        model = await WelcomeFareWellModel.find_one(WelcomeFareWellModel.guild_id == member.guild.id)
        if not model:
            return None
        return model.farewell_message
