from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_or_create(
        self,
        telegram_id: int,
        **kwargs,
    ) -> User:
        """
        Retrieves a user by telegram_id or creates a new one.
        If the user exists, it updates their profile information.
        The session must be committed by the Unit of Work.
        """
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        instance = result.scalars().first()

        if instance:
            # If user exists, update their details
            await self.update(instance, **kwargs)
            return instance

        # If no user is found, create a new one
        return await self.create(telegram_id=telegram_id, **kwargs)
