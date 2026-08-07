from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

CALLBACK_PREFIX = "health_check"

MIN_RATING = 1
MAX_RATING = 5

POLL_TEXT = (
    "🌅 Как ты себя чувствуешь сегодня?\n"
    "Нажми цифру от 1 до 5 (5 — отлично, 1 — очень плохо)."
)


def build_rating_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for rating in range(MIN_RATING, MAX_RATING + 1):
        builder.button(
            text=str(rating),
            callback_data=f"{CALLBACK_PREFIX}:{rating}",
        )
    builder.adjust(MAX_RATING)
    return builder.as_markup()


def parse_rating(callback_data: str) -> int | None:
    prefix, _, value = callback_data.partition(":")
    if prefix != CALLBACK_PREFIX or not value.isdigit():
        return None
    rating = int(value)
    if MIN_RATING <= rating <= MAX_RATING:
        return rating
    return None
