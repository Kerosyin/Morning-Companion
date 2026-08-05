from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from app.db.models import User
from app.db.uow import IUnitOfWork


@dataclass(slots=True)
class ReminderDecision:
    should_send: bool
    reminder_number: int = 0
    notify_admin: bool = False


class MorningService:
    """
    Determines what should happen during the morning workflow.
    """

    START_TIME = time(9, 0)
    END_TIME = time(12, 0)

    REMINDER_INTERVAL_MINUTES = 15

    MAX_REMINDERS = 12

    async def evaluate(
        self,
        uow: IUnitOfWork,
        user: User,
        now: datetime,
    ) -> ReminderDecision:

        if not (self.START_TIME <= now.time() < self.END_TIME):
            return ReminderDecision(False)

        activity = await uow.daily_activity.get_or_create_today(user.id)

        if activity.first_message_at is not None:
            return ReminderDecision(False)

        reminder_number = activity.reminders_sent

        expected_minutes = reminder_number * self.REMINDER_INTERVAL_MINUTES

        current_minutes = (
            now.hour * 60
            + now.minute
            - self.START_TIME.hour * 60
        )

        if current_minutes < expected_minutes:
            return ReminderDecision(False)

        if reminder_number >= self.MAX_REMINDERS:

            return ReminderDecision(
                should_send=False,
                notify_admin=not activity.admin_notified,
            )

        return ReminderDecision(
            should_send=True,
            reminder_number=reminder_number + 1,
        )