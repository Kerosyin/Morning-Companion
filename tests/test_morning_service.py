from datetime import datetime

import pytest

from app.services.morning_service import MorningService

pytestmark = pytest.mark.asyncio


class MockActivity:
    def __init__(self, first_message_at=None, reminders_sent=0, admin_notified=False):
        self.first_message_at = first_message_at
        self.reminders_sent = reminders_sent
        self.admin_notified = admin_notified


class MockUow:
    def __init__(self, activity):
        self._activity = activity

    @property
    def daily_activity(self):
        return MockUow.Repo(self._activity)

    class Repo:
        def __init__(self, activity):
            self._activity = activity

        async def get_or_create_today(self, *a):
            return self._activity


class MockUser:
    id = 1


async def _evaluate(now: datetime, reminders_sent: int = 0):
    service = MorningService()
    uow = MockUow(MockActivity(reminders_sent=reminders_sent))
    return await service.evaluate(uow=uow, user=MockUser(), now=now)


async def test_first_reminder_at_900():
    r = await _evaluate(datetime(2026, 1, 1, 9, 0))
    assert r.should_send is True
    assert r.reminder_number == 1


async def test_no_reminder_before_window():
    r = await _evaluate(datetime(2026, 1, 1, 8, 59))
    assert r.should_send is False


async def test_no_reminder_before_interval_elapsed():
    r = await _evaluate(datetime(2026, 1, 1, 9, 20), reminders_sent=1)
    assert r.should_send is False


async def test_10th_reminder_at_1155():
    r = await _evaluate(datetime(2026, 1, 1, 11, 55), reminders_sent=9)
    assert r.should_send is True
    assert r.reminder_number == 10
