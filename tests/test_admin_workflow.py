from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from aiogram.exceptions import TelegramAPIError

from app.workflows.admin_workflow import AdminWorkflow

pytestmark = pytest.mark.asyncio


class MockBot:
    def __init__(self, *, fail_on_call=None):
        self.fail_on_call = fail_on_call
        self.calls = 0
        self.sent = []

    async def send_message(self, chat_id, text=None, **kwargs):
        self.calls += 1
        if self.fail_on_call is not None and self.calls == self.fail_on_call:
            raise TelegramAPIError("sendMessage", "transient network error")
        self.sent.append(chat_id)


async def _make_user(uow, telegram_id: int) -> int:
    async with uow:
        user = await uow.users.get_or_create(
            telegram_id, defaults={"first_name": "T"}
        )
        await uow.commit()
        return user.id


async def test_failed_notify_for_one_user_does_not_rollback_others(uow, monkeypatch):
    """Bug 5: an admin-notification send failure for one user must not roll
    back the admin_notified flag of users already notified (would otherwise
    produce duplicate notifications on the next run)."""
    import app.workflows.admin_workflow as aw

    monkeypatch.setattr(
        aw,
        "now_in_timezone",
        lambda: datetime(2026, 1, 1, 13, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    user1 = await _make_user(uow, 100)
    user2 = await _make_user(uow, 200)

    bot = MockBot(fail_on_call=1)
    workflow = AdminWorkflow(
        bot=bot, admin_id=999, uow_factory=lambda: uow
    )

    await workflow.execute()

    assert 999 in bot.sent

    async with uow:
        a1 = await uow.daily_activity.get_or_create_today(user1)
        a2 = await uow.daily_activity.get_or_create_today(user2)

    assert a1.admin_notified is False
    assert a2.admin_notified is True
