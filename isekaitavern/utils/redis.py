import typing

T = typing.TypeVar("T")


def validate_async(value: typing.Any | typing.Awaitable[T]) -> typing.Awaitable[T]:
    """Extract async value from a redis response."""
    if not isinstance(value, typing.Awaitable):
        raise TypeError(f"Expected Awaitable, got {type(value), value}")
    return value
