import enum
from typing import Self


class ColorEnums(enum.Enum):
    teal = 0x1ABC9C
    dark_teal = 0x11806A
    brand_green = 0x57F287
    green = 0x2ECC71
    dark_green = 0x1F8B4C
    blue = 0x3498DB
    dark_blue = 0x206694
    purple = 0x9B59B6
    dark_purple = 0x71368A
    magenta = 0xE91E63
    dark_magenta = 0xAD1457
    gold = 0xF1C40F
    dark_gold = 0xC27C0E
    orange = 0xE67E22
    dark_orange = 0xA84300
    brand_red = 0xED4245
    red = 0xE74C3C
    dark_red = 0x992D22
    lighter_grey = 0x95A5A6
    lighter_gray = 0x95A5A6
    dark_grey = 0x607D8B
    dark_gray = 0x607D8B
    light_grey = 0x979C9F
    light_gray = 0x979C9F
    darker_grey = 0x546E7A
    darker_gray = 0x546E7A
    og_blurple = 0x7289DA
    blurple = 0x5865F2
    greyple = 0x99AAB5
    ash_theme = 0x2E2E34
    dark_theme = 0x1A1A1E
    onyx_theme = 0x070709
    light_theme = 0xFBFBFB
    fuchsia = 0xEB459E
    yellow = 0xFEE75C
    ash_embed = 0x37373E
    dark_embed = 0x242429
    onyx_embed = 0x131416
    light_embed = 0xFFFFFF
    pink = 0xEB459F

    @classmethod
    def from_str(cls, color_name: str) -> Self | None:
        if color_name in ColorEnums.__members__:
            return cls.__members__[color_name]
        return None
