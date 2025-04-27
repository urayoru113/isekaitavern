import typing

T = typing.TypeVar("T")


def ensure_awaitable(o: typing.Any | typing.Awaitable[T]) -> typing.Awaitable[T]:
    """Ensure that the obj is an Awaitable."""
    if not isinstance(o, typing.Awaitable):
        raise TypeError(f"Expected Awaitable, got {type(o), o}")
    return o


def user_id_to_name(user_id: int | str) -> str:
    """Conver user id to mention string."""
    return f"<@{user_id}>"


def channel_id_to_name(channel_id: int | str) -> str:
    """Convert channel id to mention string."""
    return f"<#{channel_id}>"
