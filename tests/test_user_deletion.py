from datetime import datetime, timezone

import pytest

from app.telegram import handlers

pytestmark = pytest.mark.asyncio


async def test_delete_by_telegram_id_removes_user_grant_and_notifications(uow):
    async with uow:
        await uow.users.get_or_create(
            123,
            defaults={"username": None, "first_name": "Test", "last_name": None},
        )
        await uow.access_grants.grant(123, granted_by=1)
        await uow.notifications.get_or_create(
            kind="morning",
            dedupe_key="delete-test",
            chat_id=123,
            text="pending",
        )
        await uow.commit()

    async with uow:
        assert await uow.users.delete_by_telegram_id(123) is True
        await uow.access_grants.revoke(123)
        await uow.notifications.delete_by_chat_id(123)
        await uow.commit()

    async with uow:
        assert await uow.users.get_by_telegram_id(123) is None
        assert await uow.access_grants.is_granted(123) is False
        assert await uow.notifications.get_by_key("morning", "delete-test") is None


class AdminMessage:
    text = "/confirm_delete 123"

    def __init__(self, admin_id):
        self.from_user = type("User", (), {"id": admin_id})()
        self.answers = []

    async def answer(self, text):
        self.answers.append(text)


async def test_confirm_delete_removes_admin_outbox_for_subject(uow, monkeypatch):
    admin_id = 900
    monkeypatch.setattr(
        handlers,
        "get_settings",
        lambda: type("Settings", (), {"admin_id": admin_id})(),
    )
    user_ids = {}
    async with uow:
        for telegram_id in (123, 456):
            user = await uow.users.get_or_create(
                telegram_id,
                defaults={
                    "username": None,
                    "first_name": "Test",
                    "last_name": None,
                },
            )
            await uow.session.flush()
            user_ids[telegram_id] = user.id
            await uow.notifications.get_or_create(
                kind="admin_inactive_user",
                dedupe_key=f"2026-09-29:{user.id}",
                chat_id=admin_id,
                text=f"User {telegram_id} is inactive",
                subject_user_id=user.id,
            )
        await uow.commit()

    handlers.pending_deletions[admin_id] = (123, datetime.now(timezone.utc))
    await handlers.confirm_delete(AdminMessage(admin_id), uow)

    async with uow:
        deleted = await uow.notifications.get_by_key(
            "admin_inactive_user", f"2026-09-29:{user_ids[123]}"
        )
        kept = await uow.notifications.get_by_key(
            "admin_inactive_user", f"2026-09-29:{user_ids[456]}"
        )
    assert deleted is None
    assert kept is not None
