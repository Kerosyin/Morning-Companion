from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

STATS_USER_PREFIX = "stats:u"
STATS_PERIOD_PREFIX = "stats:p"

_PERIODS = [7, 14, 30]
_DEFAULT_DAYS = 7
_MAX_DAYS = 365


def build_user_list_keyboard(users) -> InlineKeyboardMarkup:
    """One button per user — admin picks whose chart to view."""
    builder = InlineKeyboardBuilder()
    for user in users:
        name = user.first_name or user.username or str(user.telegram_id)
        builder.button(
            text=name,
            callback_data=f"{STATS_USER_PREFIX}:{user.telegram_id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def build_period_keyboard(
    telegram_id: int,
    current_days: int,
) -> InlineKeyboardMarkup:
    """Period switcher buttons shown under the chart."""
    builder = InlineKeyboardBuilder()
    for days in _PERIODS:
        marker = "• " if days == current_days else ""
        builder.button(
            text=f"{marker}{days} дн.",
            callback_data=f"{STATS_PERIOD_PREFIX}:{telegram_id}:{days}",
        )
    builder.adjust(len(_PERIODS))
    return builder.as_markup()


def parse_stats_callback(
    data: str,
) -> tuple[str, int, int] | None:
    """Parse ``stats:<kind>:<telegram_id>[:<days>]`` callback data.

    Returns ``(kind, telegram_id, days)`` where *kind* is ``"user"``
    or ``"period"``, or *None* if the format is unrecognised.
    """
    parts = data.split(":")
    if len(parts) < 3:
        return None
    kind = parts[1]
    if kind == "u" and len(parts) == 3 and parts[2].isdigit():
        return ("user", int(parts[2]), _DEFAULT_DAYS)
    if (
        kind == "p"
        and len(parts) == 4
        and parts[2].isdigit()
        and parts[3].isdigit()
    ):
        days = min(int(parts[3]), _MAX_DAYS)
        return ("period", int(parts[2]), days)
    return None
