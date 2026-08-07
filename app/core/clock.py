from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def app_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def now_in_timezone() -> datetime:
    return datetime.now(app_timezone())


def today_in_timezone() -> date:
    return now_in_timezone().date()
