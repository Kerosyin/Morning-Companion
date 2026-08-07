import pytest

from app.telegram.middleware.rate_limit import RateLimitMiddleware

pytestmark = pytest.mark.asyncio


class FakeUser:
    def __init__(self, id_: int):
        self.id = id_


async def _handler(event, data):
    return "ok"


async def test_under_limit_passes():
    mw = RateLimitMiddleware(max_messages=3, window_seconds=60)

    for _ in range(3):
        result = await mw(_handler, None, {"event_from_user": FakeUser(1)})
        assert result == "ok"


async def test_over_limit_blocked():
    """A user exceeding the quota is silently dropped (None, no handler call)."""
    mw = RateLimitMiddleware(max_messages=2, window_seconds=60)

    assert await mw(_handler, None, {"event_from_user": FakeUser(2)}) == "ok"
    assert await mw(_handler, None, {"event_from_user": FakeUser(2)}) == "ok"
    result = await mw(_handler, None, {"event_from_user": FakeUser(2)})
    assert result is None


async def test_missing_user_passes():
    mw = RateLimitMiddleware(max_messages=1, window_seconds=60)
    assert await mw(_handler, None, {}) == "ok"


async def test_different_users_have_independent_quotas():
    mw = RateLimitMiddleware(max_messages=1, window_seconds=60)

    assert await mw(_handler, None, {"event_from_user": FakeUser(10)}) == "ok"
    assert await mw(_handler, None, {"event_from_user": FakeUser(11)}) == "ok"
    # user 10 exhausted, user 11 still fine
    assert await mw(_handler, None, {"event_from_user": FakeUser(10)}) is None
    assert await mw(_handler, None, {"event_from_user": FakeUser(11)}) is None
