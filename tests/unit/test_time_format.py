from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.time_format import format_intake_datetime


def test_format_intake_datetime_uses_timezone():
    utc = datetime(2026, 6, 5, 5, 0, tzinfo=timezone.utc)
    formatted = format_intake_datetime(utc, tz=ZoneInfo("Europe/Moscow"))
    assert formatted == "05.06.2026 08:00"
