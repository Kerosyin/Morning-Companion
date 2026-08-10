from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationOutbox, NotificationStatus
from app.repositories.base_repository import BaseRepository


class NotificationOutboxRepository(BaseRepository[NotificationOutbox]):
    def __init__(self, session: AsyncSession):
        super().__init__(NotificationOutbox, session)

    async def get_by_key(
        self,
        kind: str,
        dedupe_key: str,
    ) -> NotificationOutbox | None:
        return await self.get_by(kind=kind, dedupe_key=dedupe_key)

    async def get_or_create(
        self,
        *,
        kind: str,
        dedupe_key: str,
        chat_id: int,
        text: str,
    ) -> NotificationOutbox:
        existing = await self.get_by_key(kind, dedupe_key)
        if existing is not None:
            return existing

        try:
            async with self.session.begin_nested():
                notification = await self.create(
                    kind=kind,
                    dedupe_key=dedupe_key,
                    chat_id=chat_id,
                    text=text,
                )
                await self.session.flush()
            return notification
        except IntegrityError:
            existing = await self.get_by_key(kind, dedupe_key)
            if existing is not None:
                return existing
            raise

    async def mark_sent(
        self,
        notification: NotificationOutbox,
    ) -> NotificationOutbox:
        return await self.update(
            notification,
            status=NotificationStatus.SENT,
            attempts=notification.attempts + 1,
            last_error=None,
            sent_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

    async def mark_failed(
        self,
        notification: NotificationOutbox,
        error: str,
    ) -> NotificationOutbox:
        return await self.update(
            notification,
            status=NotificationStatus.FAILED,
            attempts=notification.attempts + 1,
            last_error=error[:1000],
        )
