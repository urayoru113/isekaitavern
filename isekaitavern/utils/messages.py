from __future__ import annotations

import typing

from ..types import ExtractedMeessage

if typing.TYPE_CHECKING:
    import discord


def extract_message(message: discord.Message) -> ExtractedMeessage:
    content = message.content
    for e in message.embeds:
        parts = []
        if e.title:
            parts.append(e.title)
        if e.description:
            parts.append(e.description)
        if parts:
            content += f"\n[discord embed: {' | '.join(parts)}]"
    return {"author": message.author.display_name, "content": content, "time": message.created_at.isoformat()}
