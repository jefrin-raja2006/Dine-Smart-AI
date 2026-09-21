from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (matches the existing DateTime columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso_utc(value: datetime | None) -> str | None:
    """Serialize a naive-UTC datetime as an ISO string the browser can parse."""
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat() + "Z"


def clip(value: str | None, max_length: int) -> str | None:
    """Trim a string so it always fits its VARCHAR column."""
    if value is None:
        return None
    value = value.strip()
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"
