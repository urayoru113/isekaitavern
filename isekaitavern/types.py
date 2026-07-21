import typing


class SupportsStr(typing.Protocol):
    def __str__(self) -> str: ...


class ExtractedMeessage(typing.TypedDict):
    author: str
    content: str
    time: str
