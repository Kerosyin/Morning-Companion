import pytest

from app.telegram.middleware.access import AccessMiddleware

pytestmark = pytest.mark.asyncio


class FakeUser:
    def __init__(self, id_: int):
        self.id = id_


class FakeEvent:
    """Minimal event exposing .answer() like aiogram Message/CallbackQuery."""

    def __init__(self):
        self.answers = []

    async def answer(self, text):
        self.answers.append(text)


async def _handler(event, data):
    return "reached"


async def test_whitelisted_user_reaches_handler():
    mw = AccessMiddleware(allowed_users=[111])

    result = await mw(
        _handler, FakeEvent(), {"event_from_user": FakeUser(111)}
    )

    assert result == "reached"


async def test_blocked_user_is_answered_and_blocked():
    """Bug 8: a stranger must receive the 'private bot' reply (via event.answer,
    not the non-existent 'event_message' key) and be blocked."""
    mw = AccessMiddleware(allowed_users=[111])
    event = FakeEvent()

    result = await mw(
        _handler, event, {"event_from_user": FakeUser(222)}
    )

    assert result is None
    assert len(event.answers) == 1
    assert "приватным" in event.answers[0]


async def test_missing_user_is_blocked():
    mw = AccessMiddleware(allowed_users=[111])
    event = FakeEvent()

    result = await mw(_handler, event, {})

    assert result is None
