from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from aiogram.exceptions import TelegramAPIError

from app.workflows.morning_workflow import MorningWorkflow

pytestmark = pytest.mark.asyncio


class MockBot:
    def __init__(self, *, fail_chat_ids=None):
        self.fail_chat_ids = set(fail_chat_ids or [])
        self.sent = []

    async def send_message(self, chat_id, text=None, **kwargs):
        if chat_id in self.fail_chat_ids:
            raise TelegramAPIError("sendMessage", "bot was blocked by the user")
        self.sent.append(chat_id)


async def _make_user(uow, telegram_id: int) -> int:
    async with uow:
        user = await uow.users.get_or_create(
            telegram_id, defaults={"first_name": "T"}
        )
        await uow.commit()
        return user.id


async def test_failed_send_for_one_user_does_not_rollback_others(uow, monkeypatch):
    """Bug 4: a send failure for one user must be isolated (commit per user);
    users already notified must keep their reminders_sent / health_check flag
    instead of being rolled back and re-notified on the next run."""
    import app.workflows.morning_workflow as mw

    monkeypatch.setattr(
        mw,
        "now_in_timezone",
        lambda: datetime(2026, 1, 1, 9, 30, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    user1 = await _make_user(uow, 100)
    user2 = await _make_user(uow, 200)

    bot = MockBot(fail_chat_ids={100})
    workflow = MorningWorkflow(bot=bot, uow_factory=lambda: uow)

    await workflow.execute()

    assert 200 in bot.sent
    assert 100 not in bot.sent

    async with uow:
        a1 = await uow.daily_activity.get_or_create_today(user1)
        a2 = await uow.daily_activity.get_or_create_today(user2)

    assert a1.reminders_sent == 0
    assert a2.reminders_sent == 1
    assert a2.health_check_sent is True
