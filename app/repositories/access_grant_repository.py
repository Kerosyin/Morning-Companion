from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessGrant
from app.repositories.base_repository import BaseRepository


class AccessGrantRepository(BaseRepository[AccessGrant]):
    def __init__(self, session: AsyncSession):
        super().__init__(AccessGrant, session)

    async def is_granted(self, telegram_id: int) -> bool:
        return await self.get_by(telegram_id=telegram_id) is not None

    async def grant(self, telegram_id: int, granted_by: int) -> bool:
        if await self.is_granted(telegram_id):
            return False
        await self.create(telegram_id=telegram_id, granted_by=granted_by)
        return True

    async def revoke(self, telegram_id: int) -> bool:
        grant = await self.get_by(telegram_id=telegram_id)
        if grant is None:
            return False
        await self.session.delete(grant)
        return True

    async def list_all(self) -> list[AccessGrant]:
        result = await self.session.execute(
            select(AccessGrant).order_by(AccessGrant.telegram_id)
        )
        return list(result.scalars().all())
