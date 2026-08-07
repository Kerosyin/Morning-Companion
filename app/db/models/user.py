from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .critical_event import CriticalEvent
    from .daily_activity import DailyActivity
    from .health_checkin import HealthCheckin
    from .memory import Memory
    from .message import Message


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    username: Mapped[str | None]
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]

    timezone: Mapped[str] = mapped_column(default="Europe/Moscow")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    messages: Mapped[List["Message"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    memories: Mapped[List["Memory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_activities: Mapped[List["DailyActivity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    critical_events: Mapped[List["CriticalEvent"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    health_checkins: Mapped[List["HealthCheckin"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
