from datetime import datetime

import discord


def format_message(template: str, member: discord.Member, include_urls: bool = False) -> str:
    """
    Format welcome/farewell message with keyword replacement.

    Supported keywords:
    Basic:
    - {member} → @Member (mention)
    - {member.name} → Josh
    - {member.display_name} → Josh (or nickname)
    - {server.name} → Server Name
    - {count} → 1234
    - {date} → 2025-12-17
    - {time} → 14:30

    Advanced:
    - {member.id} → 123456789
    - {server.id} → 987654321
    - {member.avatar} → Avatar URL (Embed only)
    - {member.banner} → Banner URL (Embed only)
    - {server.icon} → Server icon URL (Embed only)
    - {server.banner} → Server banner URL (Embed only)
    - {server.avatar} → Guild-specific avatar URL (Embed only)

    Args:
        template: Message template with keywords
        member: Discord Member object
        include_urls: Whether to replace image URL keywords
                     - True: Replace with actual URLs (for Embed fields only)
                     - False: Replace with empty string (default, for text messages)

    Returns:
        Formatted message string

    Examples:
        >>> format_message("Welcome {member} to {server.name}!", member)
        "Welcome @Josh to MyServer!"

        >>> format_message("{member.avatar}", member, include_urls=True)
        "https://cdn.discordapp.com/avatars/..."
    """
    now = datetime.now()

    variables = {
        # Basic - Member info
        "member": member.mention,
        "member.name": member.name,
        "member.display_name": member.display_name,
        # Basic - Server info
        "server.name": member.guild.name,
        "count": str(member.guild.member_count),
        # Basic - Time info
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        # Advanced - IDs
        "member.id": str(member.id),
        "server.id": str(member.guild.id),
        # Advanced - Image URLs (Embed only)
        "member.avatar": member.display_avatar.url if include_urls else "",
        "member.banner": (member.display_banner.url if member.display_banner else "") if include_urls else "",
        "server.icon": (member.guild.icon.url if member.guild.icon else "") if include_urls else "",
        "server.banner": (member.guild.banner.url if member.guild.banner else "") if include_urls else "",
        "server.avatar": (member.guild_avatar.url if member.guild_avatar else "") if include_urls else "",
    }

    # Sort by key length (descending) to avoid partial replacements
    # e.g., replace {member.name} before {member}
    result = template
    for key in sorted(variables.keys(), key=len, reverse=True):
        result = result.replace(f"{{{key}}}", variables[key])

    return result
