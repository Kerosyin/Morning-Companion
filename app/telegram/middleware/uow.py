from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.session import SessionLocal
from app.db.uow import IUnitOfWork, UnitOfWork


class UoWMiddleware(BaseMiddleware):
    """

    Provides a UnitOfWork instance to the handler.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        uow: IUnitOfWork = UnitOfWork(SessionLocal)
        data["uow"] = uow
        return await handler(event, data)
