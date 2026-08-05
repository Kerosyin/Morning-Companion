from __future__ import annotations

import logging

logger = logging.getLogger("morning_companion")


class CleanupWorkflow:
    """
    Removes old records (currently messages) that exceed the retention period.
    """

    def __init__(self, uow_factory, retention_days: int) -> None:
        self.uow_factory = uow_factory
        self.retention_days = retention_days

    async def execute(self) -> None:
        async with self.uow_factory() as uow:
            deleted = await uow.messages.delete_older_than(self.retention_days)
            await uow.commit()

        if deleted:
            logger.info(
                "Очистка: удалено %d сообщения старше %d дней",
                deleted,
                self.retention_days,
            )