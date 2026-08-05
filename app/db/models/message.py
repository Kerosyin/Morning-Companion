from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, func, Text, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .user import User


class MessageRole(str, Enum):
    """Defines the role of a message in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    role: Mapped[MessageRole] = mapped_column(
        SqlEnum(
            MessageRole,
            name="message_role",
            native_enum=False,
            values_callable=lambda members: [member.value for member in members],
        )
    )
    text: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="messages")