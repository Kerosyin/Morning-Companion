from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HealthCheckin
from app.repositories.base_repository import BaseRepository


class HealthCheckinRepository(BaseRepository[HealthCheckin]):
    def __init__(self, session: AsyncSession):
        super().__init__(HealthCheckin, session)

    async def get_for_user_date(
        self, user_id: int, day: date
    ) -> HealthCheckin | None:
        return await self.get_by(user_id=user_id, date=day)

    async def create_or_update(
        self, user_id: int, day: date, rating: int
    ) -> HealthCheckin:
        existing = await self.get_for_user_date(user_id, day)
        if existing is not None:
            return await self.update(existing, rating=rating)
        checkin = await self.create(user_id=user_id, date=day, rating=rating)
        await self.session.flush()
        return checkin

    async def get_recent(self, user_id: int, days: int = 7) -> list[HealthCheckin]:
        since = date.today() - timedelta(days=days - 1)
        result = await self.session.execute(
            select(HealthCheckin)
            .where(
                HealthCheckin.user_id == user_id,
                HealthCheckin.date >= since,
            )
            .order_by(HealthCheckin.date)
        )
        return list(result.scalars().all())
