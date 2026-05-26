import re


def validate_utc_timezone(user_input: str) -> str | None:
    if not user_input:
        return None

    clean_input = user_input.strip().upper()

    if clean_input in ("UTC", "GMT"):
        return "UTC+0"

    pattern = r"^(?:UTC|GMT)([+-])(\d{1,2})$"
    match = re.match(pattern, clean_input)

    if not match:
        return None

    sign = match.group(1)
    offset = int(match.group(2))

    if sign == "+" and 0 <= offset <= 14:
        return f"UTC+{offset}"
    elif sign == "-" and 1 <= offset <= 12:
        return f"UTC-{offset}"

    return None
