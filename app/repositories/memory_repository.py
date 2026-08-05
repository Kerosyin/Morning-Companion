from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Memory, User
from app.repositories.base_repository import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    def __init__(self, session: AsyncSession):
        super().__init__(Memory, session)

    async def get_all_for_user(self, user: User) -> list[Memory]:
        """
        Retrieves all memories for a user.
        """
        result = await self.session.execute(
            select(self.model)
            .where(self.model.user_id == user.id)
            .order_by(self.model.created_at)
        )
        return result.scalars().all()

    async def get_memory(self, user: User, key: str) -> Memory | None:
        """
        Retrieves a specific memory for a user by its key.
        """
        return await self.get_by(user_id=user.id, key=key)

    async def set_memory(self, user: User, key: str, value: str) -> Memory:
        """
        Creates or updates a memory for a user.
        The session must be committed by the Unit of Work.
        """
        memory = await self.get_memory(user, key)
        if memory:
            return await self.update(memory, value=value)

        return await self.create(user_id=user.id, key=key, value=value)
