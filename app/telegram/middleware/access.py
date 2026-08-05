from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class AccessMiddleware(BaseMiddleware):
    """
    Blocks updates from users who are not in the allowed (whitelist) set.
    """

    def __init__(self, allowed_users: list[int]):
        self.allowed_users: set[int] = set(allowed_users)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None and user.id in self.allowed_users:
            return await handler(event, data)

        message = data.get("event_message")
        if message is not None:
            try:
                await message.answer("⛔ Извините, этот бот является приватным.")
            except Exception:
                pass

        return None
