import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger("morning_companion")


class AccessMiddleware(BaseMiddleware):
    """
    Blocks updates from users who are not in the allowed (whitelist) set.
    """

    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            if user.id == self.admin_id:
                return await handler(event, data)

            uow = data.get("uow")
            if uow is not None:
                async with uow:
                    if await uow.access_grants.is_granted(user.id):
                        return await handler(event, data)

        answer = getattr(event, "answer", None)
        if answer is not None:
            try:
                await answer("⛔ Извините, этот бот является приватным.")
            except Exception as exc:  # noqa: BLE001
                user_id = getattr(user, "id", None)
                logger.debug(
                    "Не удалось ответить заблокированному user=%s: %s",
                    user_id,
                    exc,
                )

        return None
