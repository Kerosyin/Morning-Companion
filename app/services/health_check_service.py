from __future__ import annotations

import logging

from app.core.clock import today_in_timezone
from app.db.uow import IUnitOfWork
from app.services.health_chart import render_health_chart

logger = logging.getLogger("morning_companion")

# Maps a rating (1-5) to a filled emoji bar out of 5 blocks.
_RATING_FILLED = {
    1: "█",
    2: "██",
    3: "███",
    4: "████",
    5: "█████",
}
_EMPTY = "░"


class HealthCheckService:
    """
    Persists daily well-being ratings and renders a simple trend report.
    """

    def __init__(self, days: int = 7):
        self.days = days

    async def save(self, uow: IUnitOfWork, user_id: int, rating: int) -> int:
        await uow.health_checkins.create_or_update(
            user_id, today_in_timezone(), rating
        )
        return rating

    async def trend(self, uow: IUnitOfWork, user_id: int) -> str:
        checkins = await uow.health_checkins.get_recent(user_id, self.days)

        if not checkins:
            return "📊 Пока нет данных о самочувствии за последние дни."

        average = sum(c.rating for c in checkins) / len(checkins)
        lines = [
            (
                f"📊 Самочувствие за последние {self.days} дн. "
                f"(записей {len(checkins)}, среднее {average:.1f}/5)"
            )
        ]
        for checkin in checkins:
            filled = _RATING_FILLED.get(checkin.rating, "█")
            bar = f"{filled}{_EMPTY * (5 - len(filled))}"
            weekend = "" if checkin.date.weekday() < 5 else " 🎉"
            lines.append(
                f"{checkin.date:%d.%m} {bar}  {checkin.rating}{weekend}"
            )

        return "\n".join(lines)

    async def chart(self, uow: IUnitOfWork, user_id: int) -> bytes | None:
        """Render a well-being trend chart as PNG bytes (None if no data)."""
        checkins = await uow.health_checkins.get_recent(user_id, self.days)
        return render_health_chart(
            checkins,
            self.days,
            end_date=today_in_timezone(),
        )
