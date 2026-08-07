import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, User

from app.ai.critical_event_detector import CriticalEvent
from app.config import get_settings
from app.container import get_container
from app.db.uow import IUnitOfWork
from app.services.dialog_service import DialogService
from app.services.health_check_service import HealthCheckService

logger = logging.getLogger("morning_companion")

router = Router()

CATEGORY_LABELS = {
    "health_emergency": "Здоровье (экстренно)",
    "health_concern": "Здоровье (тревога)",
    "fire": "Пожар",
    "flood": "Затопление",
    "crime": "Криминал/угроза",
    "accident": "Несчастный случай",
    "crisis_concern": "Кризис",
    "other": "Прочее",
}


@router.message(CommandStart())
async def start(message: Message):
    logger.info("User %s started the bot", message.from_user.id)
    await message.answer(
        "Добро пожаловать в Morning Companion ☀️\n\n"
        "Я готов записывать наши с вами диалоги."
    )


@router.message(Command("stats"))
async def stats(message: Message, uow: IUnitOfWork):
    """
    Shows well-being statistics. The admin can view any user's stats by
    passing a telegram_id (e.g. /stats 123456), everyone else sees their own.
    """
    async with uow:
        target = message.from_user.id
        if message.from_user.id == get_settings().admin_id:
            command_parts = message.text.split()
            if len(command_parts) > 1 and command_parts[1].isdigit():
                target = int(command_parts[1])

        user = await uow.users.get_by_telegram_id(target)
        if user is None:
            await message.answer("Пользователь с таким ID не найден.")
            return

        text = await HealthCheckService().trend(uow, user.id)

    await message.answer(text)


@router.message()
async def process_user_message(message: Message, uow: IUnitOfWork):
    """
    Handles any user message, processes it via DialogService, and sends a reply.
    """
    # In the future, this will be handled by a proper DI container
    logger.info(
        "Получено сообщение от %s: %s",
        message.from_user.id,
        message.text or message.content_type,
    )

    try:
        service: DialogService = get_container().dialog_service()
        result = await service.process_message(uow, message)
    except Exception:  # noqa: BLE001
        logger.exception("Ошибка обработки сообщения от %s", message.from_user.id)
        await message.answer("Что-то пошло не так 😔 Попробуй написать ещё раз.")
        return

    await message.answer(result.reply)

    if result.critical_event is not None:
        await _notify_admin(message.bot, message.from_user, result.critical_event)

    logger.info("Отправлен ответ пользователю %s", message.from_user.id)


def _record_admin_notify(message: str) -> None:
    """Belt-and-suspenders visibility for delivery attempts regardless of
    how the central logging is configured at runtime."""
    try:
        path = Path("data/logs")
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "admin_notify.log", "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().isoformat(timespec='seconds')} | {message}\n")
    except Exception:  # noqa: BLE001
        pass


async def _notify_admin(bot: Bot, user: User, event: CriticalEvent) -> None:
    """
    Sends a critical-event alert to the configured administrator.

    Sent as plain text (no HTML/`tg://` links) so Telegram always accepts it.
    """
    admin_id = get_settings().admin_id
    username = f"@{user.username}" if user.username else "не указан"
    name = user.first_name or user.username or str(user.id)
    category = CATEGORY_LABELS.get(event.event_type, event.event_type)
    text = (
        "🚨 Критичное сообщение от пользователя\n\n"
        f"Имя: {name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n\n"
        f"Категория: {category}\n"
        f"Уровень: {event.severity.value}\n"
        f"Суть: {event.description}\n\n"
        "Пожалуйста, свяжитесь с пользователем."
    )
    _record_admin_notify(f"send critical alert to admin={admin_id}")
    try:
        await bot.send_message(chat_id=admin_id, text=text)
        logger.info("Отправлено уведомление о критичном событии админу")
        _record_admin_notify("OK: alert sent")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Не удалось отправить уведомление админу")
        _record_admin_notify(f"FAILED: {exc!r}")
