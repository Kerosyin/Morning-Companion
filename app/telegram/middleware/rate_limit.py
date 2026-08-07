import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class RateLimitMiddleware(BaseMiddleware):
    """Per-user sliding-window rate limiter (in-memory, single-process).

    Drops messages from a user who exceeds `max_messages` within the last
    `window_seconds`. Returns None (the handler is not called), which under
    aiogram simply stops processing the update — the user gets no reply and,
    importantly, no LLM/DB work is performed. Stateless bots only: the window
    is kept in process memory.
    """

    def __init__(
        self,
        max_messages: int = 10,
        window_seconds: int = 60,
    ):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._hits: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            cutoff = now - self.window_seconds
            recent = [t for t in self._hits[user.id] if t > cutoff]
            if len(recent) >= self.max_messages:
                return None
            recent.append(now)
            self._hits[user.id] = recent
        return await handler(event, data)
