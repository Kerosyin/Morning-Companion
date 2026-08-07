import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramAPIError

from app.core.application import Application

pytestmark = pytest.mark.asyncio


def _make_app(start_polling) -> Application:
    dispatcher = MagicMock()
    dispatcher.start_polling = start_polling
    return Application(
        bot=MagicMock(),
        dispatcher=dispatcher,
        uow_factory=lambda: None,
        admin_id=1,
        retention_days=365,
    )


async def test_polling_exits_on_normal_return(monkeypatch):
    """Bug 6: when start_polling returns normally (graceful stop_polling),
    the loop must break instead of restarting forever."""
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    calls = 0

    async def start_polling(bot):
        nonlocal calls
        calls += 1
        return None

    app = _make_app(start_polling)
    await app._polling_loop()

    assert calls == 1


async def test_polling_retries_on_transient_error(monkeypatch):
    """A transient TelegramAPIError is retried, then the loop exits on success."""
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    calls = 0

    async def start_polling(bot):
        nonlocal calls
        calls += 1
        if calls < 2:
            raise TelegramAPIError("getUpdates", "server error")
        return None

    app = _make_app(start_polling)
    await app._polling_loop()

    assert calls == 2


async def test_polling_reraises_cancelled_error():
    """CancelledError must propagate (graceful shutdown signal), not be swallowed."""

    async def start_polling(bot):
        raise asyncio.CancelledError()

    app = _make_app(start_polling)
    with pytest.raises(asyncio.CancelledError):
        await app._polling_loop()
