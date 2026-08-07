from aiogram import Dispatcher

from app.config import get_settings
from app.telegram.callback_handlers import router as callback_router
from app.telegram.handlers import router
from app.telegram.middleware.access import AccessMiddleware
from app.telegram.middleware.rate_limit import RateLimitMiddleware
from app.telegram.middleware.uow import UoWMiddleware


def create_dispatcher(allowed_users: list[int]) -> Dispatcher:
    dp = Dispatcher()
    settings = get_settings()

    # In aiogram 3 the first registered middleware is the outermost one.
    # Order: UoW (construct) -> Access (drop strangers) -> RateLimit (drop
    # spammers) -> handler. So a flooding whitelisted user is stopped before
    # any DB/LLM work happens inside the handler.
    dp.message.middleware(UoWMiddleware())
    dp.message.middleware(AccessMiddleware(allowed_users))
    dp.message.middleware(
        RateLimitMiddleware(
            max_messages=settings.rate_limit_max_messages,
            window_seconds=settings.rate_limit_window_seconds,
        )
    )
    dp.callback_query.middleware(UoWMiddleware())
    dp.callback_query.middleware(AccessMiddleware(allowed_users))

    dp.include_router(router)
    dp.include_router(callback_router)

    return dp
