# utils/i18n.py
import json
from pathlib import Path

type MessageDict = dict[str, str | MessageDict]
_MESSAGE_DIR = Path(__file__).parent
_CACHE: MessageDict = {}


def get(lang: str, key: str, *args, **kwargs) -> str:
    """Get translated message

    Args:
        lang: Language code (e.g., "zh-TW", "en")
        key: Message key with dot notation (e.g., "welcome.commands.enable.success")

    Returns:
        Translated message string

    Examples:
        >>> i18n("zh-TW", "welcome.commands.enable.success")
        "✅ Enabled welcome message"
    """
    # Load language file if not cached
    if lang not in _CACHE:
        _load_language(lang)

    # Get nested value
    value = _CACHE[lang]
    for k in key.split("."):
        if isinstance(value, dict):
            value = value.get(k)
        else:
            raise KeyError(f"Invalid key: {lang}:{key}")

    if not isinstance(value, str):
        raise TypeError(f"Expected str, got {type(value), value}")

    return value.format(*args, **kwargs)


def _load_language(lang: str) -> None:
    """Load language file into cache

    Args:
        lang: Language code

    Raises:
        FileNotFoundError: If language file doesn't exist
    """
    file = _MESSAGE_DIR.joinpath(f"{lang}.json")
    if not file.is_file():
        raise FileNotFoundError(f"Language file not found: {file}")

    with file.open(encoding="utf-8") as f:
        _CACHE[lang] = json.load(f)


def reload(lang: str | None = None) -> None:
    """Reload language files

    Args:
        lang: Specific language to reload, or None to reload all
    """
    if lang:
        _CACHE.pop(lang)
    else:
        _CACHE.clear()
