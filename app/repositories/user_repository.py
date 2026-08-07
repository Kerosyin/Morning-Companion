from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_telegram_id(
        self,
        telegram_id: int,
    ) -> User | None:

        return await self.get_by(
            telegram_id=telegram_id,
        )

    async def get_or_create(
        self,
        telegram_id: int,
        defaults: dict,
    ) -> User:

        user = await self.get_by_telegram_id(
            telegram_id,
        )

        if user:
            return user

        try:
            async with self.session.begin_nested():
                user = await self.create(
                    telegram_id=telegram_id,
                    **defaults,
                )
                await self.session.flush()
            return user
        except IntegrityError:
            user = await self.get_by_telegram_id(telegram_id)
            if user is not None:
                return user
            raise

    async def get_all(self) -> list[User]:
        """
        Returns all registered users.
        """

        result = await self.session.execute(
            select(User)
            .order_by(User.id)
        )

        return list(result.scalars().all())
