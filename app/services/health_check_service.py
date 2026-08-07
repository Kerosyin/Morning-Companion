from __future__ import annotations

import logging
from datetime import date

from app.db.uow import IUnitOfWork

logger = logging.getLogger("morning_companion")

# Maps a rating (1-5) to a filled emoji bar out of 5 blocks.
_RATING_FILLED = {
    1: "█",
    2: "█",
    3: "██",
    4: "███",
    5: "████",
}
_FULL = "█████"


class HealthCheckService:
    """
    Persists daily well-being ratings and renders a simple trend report.
    """

    def __init__(self, days: int = 7):
        self.days = days

    async def save(self, uow: IUnitOfWork, user_id: int, rating: int) -> int:
        await uow.health_checkins.create_or_update(user_id, date.today(), rating)
        return rating

    async def trend(self, uow: IUnitOfWork, user_id: int) -> str:
        checkins = await uow.health_checkins.get_recent(user_id, self.days)

        if not checkins:
            return "📊 Пока нет данных о самочувствии за последние дни."

        average = sum(c.rating for c in checkins) / len(checkins)
        lines = [f"📊 Самочувствие за {len(checkins)} дн. (среднее {average:.1f}/5)"]
        for checkin in checkins:
            filled = _RATING_FILLED.get(checkin.rating, "█")
            weekend = "" if checkin.date.weekday() < 5 else " 🎉"
            lines.append(
                f"{checkin.date:%d.%m} {filled}{_FULL[len(filled):]}"
                f"  {checkin.rating}{weekend}"
            )

        return "\n".join(lines)
