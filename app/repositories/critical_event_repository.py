from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CriticalEvent
from app.repositories.base_repository import BaseRepository


class CriticalEventRepository(BaseRepository[CriticalEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(CriticalEvent, session)

    async def get_last_for_user(self, user_id: int) -> CriticalEvent | None:
        """
        Returns the most recent critical event for a user, if any.
        """
        stmt = (
            select(CriticalEvent)
            .where(CriticalEvent.user_id == user_id)
            .order_by(CriticalEvent.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_event(self, **kwargs) -> CriticalEvent:
        """
        Creates a critical event and flushes so the id is available.
        """
        event = await self.create(**kwargs)
        await self.session.flush()
        return event
