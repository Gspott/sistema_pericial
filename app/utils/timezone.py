from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


MADRID_TZ = ZoneInfo("Europe/Madrid")
UTC_TZ = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC_TZ)


def now_madrid() -> datetime:
    return now_utc().astimezone(MADRID_TZ)


def today_madrid() -> date:
    return now_madrid().date()


def now_utc_iso(timespec: str = "seconds") -> str:
    return now_utc().isoformat(timespec=timespec)


def now_madrid_iso(timespec: str = "seconds") -> str:
    return now_madrid().isoformat(timespec=timespec)


def datetime_local_madrid_minutes() -> str:
    return now_madrid().strftime("%Y-%m-%dT%H:%M")


def timestamp_filename_madrid() -> str:
    return now_madrid().strftime("%Y%m%d_%H%M%S")


def parse_timestamp(value, assume_naive_tz=UTC_TZ) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        if " " in text and "T" not in text:
            text = text.replace(" ", "T", 1)
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=assume_naive_tz)
    return parsed


def to_madrid(value, assume_naive_tz=UTC_TZ) -> datetime | None:
    parsed = parse_timestamp(value, assume_naive_tz=assume_naive_tz)
    if parsed is None:
        return None
    return parsed.astimezone(MADRID_TZ)


def format_date_madrid(value=None, default: str = "") -> str:
    if value is None:
        return today_madrid().strftime("%d/%m/%Y")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    converted = to_madrid(value)
    if converted is None:
        return default
    return converted.strftime("%d/%m/%Y")


def format_datetime_madrid(value, default: str = "", include_seconds: bool = False) -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        try:
            return datetime.strptime(text, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return default
    converted = to_madrid(text)
    if converted is None:
        return default
    formato = "%d/%m/%Y %H:%M:%S" if include_seconds else "%d/%m/%Y %H:%M"
    return converted.strftime(formato)
