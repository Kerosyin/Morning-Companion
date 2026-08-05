import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.container import get_container
from app.db.uow import IUnitOfWork
from app.services.dialog_service import DialogService

logger = logging.getLogger("morning_companion")

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    logger.info("User %s started the bot", message.from_user.id)
    await message.answer(
        "Добро пожаловать в Morning Companion ☀️\n\n"
        "Я готов записывать наши с вами диалоги."
    )


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
        response_text = await service.process_message(uow, message)
    except Exception:  # noqa: BLE001
        logger.exception("Ошибка обработки сообщения от %s", message.from_user.id)
        await message.answer("Что-то пошло не так 😔 Попробуй написать ещё раз.")
        return

    await message.answer(response_text)

    logger.info("Отправлен ответ пользователю %s", message.from_user.id)
