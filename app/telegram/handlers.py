from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db.uow import IUnitOfWork
from app.services.dialog_service import DialogService

router = Router()


@router.message(CommandStart())
async def start(message: Message):
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
    service = DialogService()
    
    response_text = await service.process_message(uow, message)
    await message.answer(response_text)
