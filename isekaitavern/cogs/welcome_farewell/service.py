import discord

from ...core.formatter import format_message
from .model import WelcomeFarewellModelT


class WelcomeFarewellService:
    @staticmethod
    def build_embed(model: WelcomeFarewellModelT, member: discord.Member) -> discord.Embed:
        embed_data = model.to_embed_dict()

        embed_data["description"] = format_message(embed_data["description"], member)
        embed_data["title"] = format_message(embed_data["title"], member)

        embed = discord.Embed(
            title=embed_data["title"], description=embed_data["description"], color=embed_data["color"]
        )
        if model.thumbnail_url:
            embed.set_thumbnail(url=format_message(model.thumbnail_url, member))
        if model.image_url:
            embed.set_image(url=format_message(model.image_url, member))

        return embed
