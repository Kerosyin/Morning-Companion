from aiogram import Dispatcher

from app.telegram.callback_handlers import router as callback_router
from app.telegram.handlers import router
from app.telegram.middleware.access import AccessMiddleware
from app.telegram.middleware.uow import UoWMiddleware


def create_dispatcher(allowed_users: list[int]) -> Dispatcher:
    dp = Dispatcher()

    # Register middlewares
    # The last registered middleware is the outermost one,
    # so AccessMiddleware wraps UoWMiddleware and blocks strangers first.
    dp.message.middleware(UoWMiddleware())
    dp.message.middleware(AccessMiddleware(allowed_users))
    dp.callback_query.middleware(UoWMiddleware())
    dp.callback_query.middleware(AccessMiddleware(allowed_users))

    dp.include_router(router)
    dp.include_router(callback_router)

    return dp
