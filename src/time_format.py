import os
from datetime import datetime
from zoneinfo import ZoneInfo


def get_app_timezone() -> ZoneInfo:
    name = os.getenv("APP_TIMEZONE", "Europe/Moscow")
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("Europe/Moscow")


def format_intake_datetime(value: datetime, tz: ZoneInfo | None = None) -> str:
    """Форматирует время приёма для уведомлений в локальной зоне приложения."""
    tz = tz or get_app_timezone()
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    local = value.astimezone(tz)
    return local.strftime("%d.%m.%Y %H:%M")
