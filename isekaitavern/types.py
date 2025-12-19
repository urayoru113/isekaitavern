import typing


class SupportsStr(typing.Protocol):
    def __str__(self) -> str: ...
