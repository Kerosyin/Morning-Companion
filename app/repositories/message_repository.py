from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def get_history(self, user: User, limit: int = 10) -> list[Message]:
        """
        Retrieves the last N messages for a user in chronological order.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user.id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        # The query returns in descending order, so we reverse the list
        # to get the correct chronological order (oldest to newest).
        return result.scalars().all()[::-1]
