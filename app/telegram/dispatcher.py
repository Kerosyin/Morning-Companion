from aiogram import Dispatcher

from app.telegram.handlers import router


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    dp.include_router(router)

    return dp
