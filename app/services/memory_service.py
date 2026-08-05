from __future__ import annotations

import logging

from app.ai.memory_extractor import MemoryExtractor
from app.ai.models import ConversationContext
from app.db.uow import IUnitOfWork

logger = logging.getLogger("morning_companion")


class MemoryService:
    """
    Updates long-term memory after each conversation.
    """

    def __init__(
        self,
        extractor: MemoryExtractor,
    ) -> None:
        self.extractor = extractor

    async def update(
        self,
        uow: IUnitOfWork,
        context: ConversationContext,
    ) -> None:

        updates = await self.extractor.extract(context)

        if not updates:
            return

        for memory in updates:

            await uow.memories.set_memory(
                user=context.user,
                key=f"{memory.category}:{memory.key}",
                value=memory.value,
            )

        logger.info(
            "Сохранено %d фактов о пользователе",
            len(updates),
        )
