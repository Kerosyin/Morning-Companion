from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InputMediaPhoto,
)

from app.config import get_settings
from app.db.uow import IUnitOfWork
from app.services.health_check_service import HealthCheckService
from app.telegram.health_poll import CALLBACK_PREFIX, parse_rating
from app.telegram.stats_keyboard import (
    build_period_keyboard,
    parse_stats_callback,
)

logger = logging.getLogger("morning_companion")

router = Router()

health_service = HealthCheckService()


@router.callback_query(F.data.startswith(f"{CALLBACK_PREFIX}:"))
async def health_rating(callback: CallbackQuery, uow: IUnitOfWork):
    rating = parse_rating(callback.data)
    if rating is None:
        await callback.answer("Некорректный ввод", show_alert=True)
        return

    async with uow:
        user = await uow.users.get_or_create(
            callback.from_user.id,
            defaults={
                "username": callback.from_user.username,
                "first_name": callback.from_user.first_name,
                "last_name": callback.from_user.last_name,
            },
        )
        await health_service.save(uow, user.id, rating)
        await uow.commit()

    try:
        await callback.message.edit_text(
            f"Спасибо! Сегодня твоё самочувствие: {rating}/5 ✅"
        )
    except (TelegramAPIError, AttributeError) as exc:
        logger.debug("edit_text в callback не выполнен: %s", exc)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("stats:"))
async def stats_callback(callback: CallbackQuery, uow: IUnitOfWork):
    """Handle admin stats callbacks: user selection and period switching."""
    parsed = parse_stats_callback(callback.data)
    if parsed is None:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    kind, telegram_id, days = parsed

    if callback.from_user.id != get_settings().admin_id:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    async with uow:
        user = await uow.users.get_by_telegram_id(telegram_id)
        if user is None:
            await callback.answer(
                "Пользователь не найден", show_alert=True
            )
            return
        service = HealthCheckService(days=days)
        text = await service.trend(uow, user.id)
        chart_png = await service.chart(uow, user.id)

    if chart_png is None:
        await callback.answer(
            "Нет данных о самочувствии", show_alert=True
        )
        return

    name = user.first_name or user.username or str(user.telegram_id)
    caption = f"📊 {name}\n{text}"
    kb = build_period_keyboard(telegram_id, days)

    if kind == "user":
        await callback.message.answer_photo(
            BufferedInputFile(chart_png, filename="stats.png"),
            caption=caption,
            reply_markup=kb,
        )
    else:
        media = InputMediaPhoto(
            media=BufferedInputFile(chart_png, filename="stats.png"),
            caption=caption,
        )
        try:
            await callback.message.edit_media(media=media, reply_markup=kb)
        except TelegramAPIError as exc:
            logger.debug("edit_media в stats callback не выполнен: %s", exc)

    await callback.answer()
