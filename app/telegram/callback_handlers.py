from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.db.uow import IUnitOfWork
from app.services.health_check_service import HealthCheckService
from app.telegram.health_poll import CALLBACK_PREFIX, parse_rating

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

    await callback.message.edit_text(
        f"Спасибо! Сегодня твоё самочувствие: {rating}/5 ✅"
    )
    await callback.answer()
