import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardMarkup,
    Message,
    User,
)

from app.ai.critical_event_detector import CriticalEvent
from app.config import get_settings
from app.container import get_container
from app.core.clock import now_in_timezone
from app.db.uow import IUnitOfWork
from app.services.dialog_service import DialogService
from app.services.health_check_service import HealthCheckService
from app.telegram.health_poll import POLL_TEXT, build_rating_keyboard
from app.telegram.stats_keyboard import (
    build_period_keyboard,
    build_user_list_keyboard,
)

logger = logging.getLogger("morning_companion")

router = Router()
pending_deletions: dict[int, tuple[int, datetime]] = {}

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


@router.message(Command("users"))
async def users_list(message: Message, uow: IUnitOfWork):
    """
    Admin-only: lists all registered users with their names and telegram ids.
    """
    if message.from_user.id != get_settings().admin_id:
        await message.answer("Эта команда доступна только администратору.")
        return

    async with uow:
        users = await uow.users.get_all()
        if not users:
            await message.answer("Пользователей пока нет.")
            return
        lines = ["👥 Пользователи:"]
        for user in users:
            name = user.first_name or (f"@{user.username}" if user.username else "—")
            lines.append(f"• {name} — {user.telegram_id}")
        text = "\n".join(lines)

    await message.answer(text)


def _admin_id(message: Message) -> int | None:
    if message.from_user.id == get_settings().admin_id:
        return message.from_user.id
    return None


def _command_telegram_id(text: str) -> int | None:
    parts = text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    telegram_id = int(parts[1])
    return telegram_id if telegram_id > 0 else None


@router.message(Command("allow"))
async def allow_access(message: Message, uow: IUnitOfWork):
    admin_id = _admin_id(message)
    if admin_id is None:
        await message.answer("Эта команда доступна только администратору.")
        return
    telegram_id = _command_telegram_id(message.text)
    if telegram_id is None:
        await message.answer("Использование: /allow <telegram_id>")
        return
    async with uow:
        added = await uow.access_grants.grant(telegram_id, granted_by=admin_id)
        await uow.commit()
    text = "Добавлен доступ для" if added else "Доступ уже есть у"
    await message.answer(f"{text} {telegram_id}.")


@router.message(Command("deny"))
async def deny_access(message: Message, uow: IUnitOfWork):
    admin_id = _admin_id(message)
    if admin_id is None:
        await message.answer("Эта команда доступна только администратору.")
        return
    telegram_id = _command_telegram_id(message.text)
    if telegram_id is None:
        await message.answer("Использование: /deny <telegram_id>")
        return
    if telegram_id == admin_id:
        await message.answer("Нельзя отозвать доступ у администратора.")
        return
    async with uow:
        removed = await uow.access_grants.revoke(telegram_id)
        await uow.commit()
    text = "Доступ отозван у" if removed else "Пользователя нет в списке:"
    await message.answer(f"{text} {telegram_id}.")


@router.message(Command("allowed"))
async def allowed_access(message: Message, uow: IUnitOfWork):
    if _admin_id(message) is None:
        await message.answer("Эта команда доступна только администратору.")
        return
    async with uow:
        grants = await uow.access_grants.list_all()
    if not grants:
        await message.answer("Список доступа пуст.")
        return
    await message.answer("Разрешённые ID:\n" + "\n".join(
        str(grant.telegram_id) for grant in grants
    ))


@router.message(Command("delete_user"))
async def delete_user(message: Message, uow: IUnitOfWork):
    admin_id = _admin_id(message)
    if admin_id is None:
        await message.answer("Эта команда доступна только администратору.")
        return
    telegram_id = _command_telegram_id(message.text)
    if telegram_id is None:
        await message.answer("Использование: /delete_user <telegram_id>")
        return
    if telegram_id == admin_id:
        await message.answer("Нельзя удалить администратора.")
        return
    pending_deletions[admin_id] = (telegram_id, datetime.now(timezone.utc))
    await message.answer(
        f"Будут безвозвратно удалены все данные {telegram_id}. "
        f"Подтвердите: /confirm_delete {telegram_id}"
    )


@router.message(Command("confirm_delete"))
async def confirm_delete(message: Message, uow: IUnitOfWork):
    admin_id = _admin_id(message)
    if admin_id is None:
        await message.answer("Эта команда доступна только администратору.")
        return
    telegram_id = _command_telegram_id(message.text)
    pending = pending_deletions.pop(admin_id, None)
    if (
        telegram_id is None
        or pending is None
        or pending[0] != telegram_id
        or datetime.now(timezone.utc) - pending[1] > timedelta(minutes=5)
    ):
        await message.answer("Нет действующего подтверждения удаления.")
        return
    async with uow:
        user = await uow.users.get_by_telegram_id(telegram_id)
        await uow.access_grants.revoke(telegram_id)
        await uow.notifications.delete_by_chat_id(telegram_id)
        if user is not None:
            await uow.notifications.delete_by_subject_user_id(user.id)
        deleted = await uow.users.delete_by_telegram_id(telegram_id)
        await uow.commit()
    text = (
        "Пользователь и все его данные удалены."
        if deleted
        else "Пользователь не найден."
    )
    await message.answer(text)


@router.message(Command("stats"))
async def stats(message: Message, uow: IUnitOfWork):
    """
    Shows well-being statistics as a chart.

    **Admin** receives a button-list of all users; tapping one opens that
    user's chart with period switchers.

    **Regular user** receives their own chart directly. An optional numeric
    argument overrides the period (e.g. ``/stats 14``).
    """
    settings = get_settings()
    is_admin = message.from_user.id == settings.admin_id

    if is_admin:
        async with uow:
            users = await uow.users.get_all()
        if not users:
            await message.answer("Нет зарегистрированных пользователей.")
            return
        await message.answer(
            "📊 Выберите пользователя:",
            reply_markup=build_user_list_keyboard(users),
        )
        return

    days = _parse_days_arg(message.text, default=7)
    async with uow:
        user = await uow.users.get_by_telegram_id(message.from_user.id)
        if user is None:
            await message.answer("Сначала отправьте сообщение боту.")
            return
        service = HealthCheckService(days=days)
        text = await service.trend(uow, user.id)
        chart_png = await service.chart(uow, user.id)
        kb = build_period_keyboard(user.telegram_id, days)

    await _send_stats(message, chart_png, text, kb)


def _parse_days_arg(text: str, default: int) -> int:
    for part in text.split()[1:]:
        if part.isdigit() and 1 <= int(part) <= 90:
            return int(part)
    return default


async def _send_stats(
    message: Message,
    png: bytes | None,
    text: str,
    kb: InlineKeyboardMarkup | None = None,
) -> None:
    if png is not None:
        await message.answer_photo(
            BufferedInputFile(png, filename="stats.png"),
            caption=text,
            reply_markup=kb,
        )
    else:
        await message.answer(text, reply_markup=kb)


@router.message()
async def process_user_message(message: Message, uow: IUnitOfWork):
    """
    Handles any user message, processes it via DialogService, and sends a reply.
    """
    logger.info(
        "Получено сообщение от %s: type=%s length=%d",
        message.from_user.id,
        message.content_type,
        len(message.text or ""),
    )

    if not message.text:
        await message.answer("Пока я умею отвечать только на текстовые сообщения.")
        return

    try:
        service: DialogService = get_container().dialog_service()
        result = await service.process_message(uow, message)
    except Exception:  # noqa: BLE001
        logger.exception("Ошибка обработки сообщения от %s", message.from_user.id)
        await message.answer("Что-то пошло не так 😔 Попробуй написать ещё раз.")
        return

    await message.answer(result.reply)

    if result.health_poll_pending and result.critical_event is None:
        await message.bot.send_message(
            chat_id=message.from_user.id,
            text=POLL_TEXT,
            reply_markup=build_rating_keyboard(),
        )
        logger.info("Отправлен health poll пользователю %s", message.from_user.id)

    _record_admin_notify(
        f"handler critical_event_present={result.critical_event is not None}"
    )

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
            fh.write(
                f"{now_in_timezone().isoformat(timespec='seconds')} | {message}\n"
            )
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
    severity = getattr(event.severity, "value", event.severity)
    text = (
        "🚨 Критичное сообщение от пользователя\n\n"
        f"Имя: {name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n\n"
        f"Категория: {category}\n"
        f"Уровень: {severity}\n"
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
