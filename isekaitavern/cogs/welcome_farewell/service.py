import discord

from ...core.formatter import format_message
from ...enums import ColorEnums
from .model import WelcomeFarewellModelT


class WelcomeFarewellService:
    @staticmethod
    def get_color(color: str) -> int | None:
        color_obj = ColorEnums.from_str(color)
        if color_obj:
            color_value = color_obj.value
        else:
            try:
                color_value = discord.Color.from_str(color).value
            except ValueError:
                return None
        return color_value

    @staticmethod
    def build_message(model: WelcomeFarewellModelT, member: discord.Member) -> discord.Embed:
        embed_data = model.to_embed_dict()

        embed_data["description"] = format_message(embed_data["description"], member)
        embed_data["title"] = format_message(embed_data["title"], member)

        embed = discord.Embed(
            title=embed_data["title"], description=embed_data["description"], color=embed_data["color"]
        )
        if model.thumbnail_url:
            embed.set_thumbnail(url=format_message(model.thumbnail_url, member, True))
        if model.image_url:
            embed.set_image(url=format_message(model.image_url, member, True))

        return embed
