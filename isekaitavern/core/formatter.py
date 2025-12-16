from datetime import datetime

import discord


def format_message(template: str, member: discord.Member) -> str:
    """
    轉譯訊息中的 keyword

    支援的 keywords:
    - {member} → @Member (mention)
    - {member.name} → Josh
    - {member.display_name} → Josh (或暱稱)
    - {member.id} → 123456789
    - {member.avatar} → https://cdn.discord.com/...
    - {server} → Server Name
    - {server.name} → Server Name
    - {server.id} → 987654321
    - {server.member_count} → 1234
    - {count} → 1234
    - {time} → 14:30
    - {date} → 2025-12-14
    - {datetime} → 2025-12-14 14:30

    Args:
        template: 訊息模板
        member: Discord 成員物件

    Returns:
        轉譯後的訊息

    Example:
        >>> format_message("歡迎 {member} 來到 {server}!", member)
        "歡迎 @Josh 來到 MyServer!"
    """
    variables = {
        # 成員相關
        "member": member.mention,
        "member.display_name": member.display_name,
        "member.name": member.name,
        "member.id": str(member.id),
        "member.avatar": member.display_avatar.url,
        "member.banner": member.display_banner.url if member.display_banner else "",
        # 伺服器相關
        "server.name": member.guild.name,
        "server.id": str(member.guild.id),
        "server.member_count": str(member.guild.member_count),
        "server.icon": member.guild.icon.url if member.guild.icon else "",
        "server.avatar": member.guild_avatar.url if member.guild_avatar else "",
        "server.banner": member.guild_banner.url if member.guild_banner else "",
        # 計數
        "count": str(member.guild.member_count),
        # 時間
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # 替換所有 keyword
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value)

    return result
