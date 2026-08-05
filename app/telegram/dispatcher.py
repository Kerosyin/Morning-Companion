from aiogram import Dispatcher

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
    # You can also register it for other update types if needed
    # dp.callback_query.middleware(UoWMiddleware())

    dp.include_router(router)

    return dp
