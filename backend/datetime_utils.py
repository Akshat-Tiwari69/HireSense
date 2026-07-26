"""Timezone-safe parsing for browser-supplied datetimes."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


def parse_client_datetime(value: str | datetime) -> datetime:
    """Return an aware UTC datetime; naive browser values are interpreted as IST."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise ValueError("An ISO datetime is required")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_TIMEZONE)
    return parsed.astimezone(timezone.utc)
