from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Добро пожаловать в Morning Companion ☀️"
    )


@router.message()
async def echo(message: Message):
    await message.answer(
        "Пока я только запускаюсь 🙂"
    )
