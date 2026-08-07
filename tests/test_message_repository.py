from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.db.models import Message

pytestmark = pytest.mark.asyncio


async def _make_user(uow, telegram_id: int) -> int:
    async with uow:
        user = await uow.users.get_or_create(
            telegram_id, defaults={"first_name": "T"}
        )
        await uow.commit()
        return user.id


async def test_delete_older_than_removes_old_messages(uow):
    """Bug 11: cutoff must be a naive UTC datetime so the string comparison
    against SQLite's naive created_at works correctly."""
    user_id = await _make_user(uow, 701)

    async with uow:
        old = await uow.messages.create(
            user_id=user_id, role="user", text="старое"
        )
        old.created_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(days=400)
        )
        recent = await uow.messages.create(
            user_id=user_id, role="user", text="свежее"
        )
        recent.created_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(days=1)
        )
        await uow.commit()

    async with uow:
        deleted = await uow.messages.delete_older_than(365)
        remaining = (
            await uow.session.execute(
                select(Message).where(Message.user_id == user_id)
            )
        ).scalars().all()
        await uow.commit()

    assert deleted == 1
    assert len(remaining) == 1
    assert remaining[0].text == "свежее"


async def test_delete_older_than_nothing_to_delete(uow):
    user_id = await _make_user(uow, 702)

    async with uow:
        msg = await uow.messages.create(
            user_id=user_id, role="user", text="недавнее"
        )
        msg.created_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(days=1)
        )
        await uow.commit()

    async with uow:
        deleted = await uow.messages.delete_older_than(365)
        await uow.commit()

    assert deleted == 0
