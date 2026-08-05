from aiogram import Dispatcher

from app.telegram.handlers import router
from app.telegram.middleware.uow import UoWMiddleware


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # Register middlewares
    dp.message.middleware(UoWMiddleware())
    # You can also register it for other update types if needed
    # dp.callback_query.middleware(UoWMiddleware())

    dp.include_router(router)

    return dp
