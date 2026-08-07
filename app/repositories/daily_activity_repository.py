from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DailyActivity
from app.repositories.base_repository import BaseRepository


class DailyActivityRepository(BaseRepository[DailyActivity]):
    def __init__(self, session: AsyncSession):
        super().__init__(DailyActivity, session)

    async def get_or_create_today(self, user_id: int) -> DailyActivity:
        """
        Gets today's activity for a user, creating one if it doesn't exist.
        """
        today = date.today()
        # Using get_by to find the specific record
        result = await self.get_by(user_id=user_id, date=today)

        if result:
            return result

        # If not found, create a new one
        activity = await self.create(user_id=user_id, date=today)
        await self.session.flush()
        return activity

    async def set_first_message_time(
        self, activity: DailyActivity, time: datetime
    ) -> DailyActivity:
        """
        Sets the first message time for a daily activity.
        """
        return await self.update(activity, first_message_at=time)

    async def increment_reminders_sent(self, activity: DailyActivity) -> DailyActivity:
        """
        Increments the reminders_sent counter for a daily activity.
        """
        return await self.update(activity, reminders_sent=activity.reminders_sent + 1)

    async def mark_health_check_sent(self, activity: DailyActivity) -> DailyActivity:
        """
        Marks that the health check prompt was sent for this activity.
        """
        return await self.update(activity, health_check_sent=True)
