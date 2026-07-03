from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


TIME_RE = r"(?P<hour>[01]?\d|2[0-3]):(?P<minute>[0-5]\d)"


def now_local(timezone_name: str) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))


def to_storage(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def from_storage(value: str, timezone_name: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(ZoneInfo(timezone_name))


def format_local(value: str | None, timezone_name: str) -> str:
    if not value:
        return "без даты"
    return from_storage(value, timezone_name).strftime("%d.%m.%Y %H:%M")


def parse_reminder_text(text: str, timezone_name: str) -> tuple[datetime | None, str]:
    text = text.strip()
    local_now = now_local(timezone_name)

    relative = re.match(
        r"^через\s+(?P<amount>\d+)\s+"
        r"(?P<unit>минут[уы]?|мин|час(?:а|ов)?|ч)\s+"
        r"(?P<title>.+)$",
        text,
        re.IGNORECASE,
    )
    if relative:
        amount = int(relative.group("amount"))
        unit = relative.group("unit").lower()
        delta = timedelta(hours=amount) if unit.startswith(("час", "ч")) else timedelta(minutes=amount)
        return local_now + delta, relative.group("title").strip()

    for word, days in (("сегодня", 0), ("завтра", 1)):
        match = re.match(
            rf"^{word}(?:\s+в)?\s+{TIME_RE}\s+(?P<title>.+)$",
            text,
            re.IGNORECASE,
        )
        if match:
            target_date = local_now.date() + timedelta(days=days)
            target = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                int(match.group("hour")),
                int(match.group("minute")),
                tzinfo=ZoneInfo(timezone_name),
            )
            if target <= local_now and days == 0:
                target += timedelta(days=1)
            return target, match.group("title").strip()

    absolute = re.match(
        rf"^(?P<date>\d{{4}}-\d{{2}}-\d{{2}})\s+{TIME_RE}\s+(?P<title>.+)$",
        text,
    )
    if absolute:
        target = datetime(
            *map(int, absolute.group("date").split("-")),
            int(absolute.group("hour")),
            int(absolute.group("minute")),
            tzinfo=ZoneInfo(timezone_name),
        )
        return target, absolute.group("title").strip()

    return None, text


def parse_todo_text(text: str, timezone_name: str) -> tuple[str, datetime | None]:
    due_at, title = parse_reminder_text(text, timezone_name)
    if due_at is None:
        return text.strip(), None
    return title, due_at


def local_day_range(timezone_name: str, *, days_ahead: int = 0) -> tuple[str, str]:
    local_now = now_local(timezone_name)
    start_date = local_now.date() + timedelta(days=days_ahead)
    start = datetime(start_date.year, start_date.month, start_date.day, tzinfo=ZoneInfo(timezone_name))
    end = start + timedelta(days=1)
    return to_storage(start), to_storage(end)


def local_week_range(timezone_name: str) -> tuple[str, str]:
    start, _ = local_day_range(timezone_name)
    end = datetime.fromisoformat(start) + timedelta(days=7)
    return start, end.isoformat()

