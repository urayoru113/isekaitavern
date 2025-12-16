import typing
from copy import deepcopy
from typing import Literal


def ensure_awaitable[T: typing.Awaitable](o: typing.Any | typing.Awaitable[T]) -> typing.Awaitable[T]:
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


def dict_deep_extend(*dicts: dict, strategy: Literal["keep", "force", "error"] = "force") -> dict:
    """
    Recursively merge multiple dictionaries with conflict resolution.

    Args:
        *dicts: Variable number of dictionaries to merge (left to right)
        strategy: Conflict resolution strategy
            - "keep": Keep leftmost value when conflict
            - "force": Use rightmost value when conflict (default)
            - "error": Raise ValueError on conflict

    Returns:
        Merged dictionary (new instance, doesn't modify inputs)

    Raises:
        ValueError: When strategy="error" and a conflict is detected
        ValueError: When no dictionaries are provided

    Example:
        >>> d1 = {'a': {'k1': 1}}
        >>> d2 = {'a': {'k1': 999, 'k2': 2}}
        >>> d3 = {'b': 3}
        >>> deep_merge(d1, d2, d3, strategy="keep")
        {'a': {'k1': 1, 'k2': 2}, 'b': 3}
        >>> deep_merge(d1, d2, d3, strategy="force")
        {'a': {'k1': 999, 'k2': 2}, 'b': 3}
    """
    if not dicts:
        raise ValueError("At least one dictionary is required")

    if len(dicts) == 1:
        return deepcopy(dicts[0])

    result = deepcopy(dicts[0])

    for override in dicts[1:]:
        for key, value in override.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    # Both are dicts, merge recursively
                    result[key] = dict_deep_extend(result[key], value, strategy=strategy)
                elif strategy == "keep":  # Conflict: not both dicts
                    pass  # Keep result[key]
                elif strategy == "force":
                    result[key] = deepcopy(value)
                elif strategy == "error":
                    raise ValueError(f"Conflict at key '{key}': {result[key]} vs {value}")
            else:
                # New key, add it
                result[key] = deepcopy(value)

    return result
