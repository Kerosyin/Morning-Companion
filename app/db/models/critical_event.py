from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User


class CriticalSeverity(str, Enum):
    """Defines the severity of a critical event reported by a user."""

    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class CriticalEvent(Base):
    __tablename__ = "critical_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    severity: Mapped[CriticalSeverity] = mapped_column(
        SqlEnum(
            CriticalSeverity,
            name="critical_severity",
            native_enum=False,
            values_callable=lambda members: [member.value for member in members],
        )
    )
    event_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    message_text: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="critical_events")
