from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User


class DailyActivity(Base):
    __tablename__ = "daily_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True, default=func.current_date())
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    first_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reminders_sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    admin_notified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    health_check_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    user: Mapped["User"] = relationship(back_populates="daily_activities")

    __table_args__ = (
        UniqueConstraint("date", "user_id", name="uq_daily_activity_date_user"),
    )
