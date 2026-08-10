import pytest
from aiogram.exceptions import TelegramAPIError

from app.telegram.callback_handlers import health_rating, stats_callback
from app.telegram.health_poll import CALLBACK_PREFIX
from app.telegram.stats_keyboard import STATS_PERIOD_PREFIX

pytestmark = pytest.mark.asyncio


class _FromUser:
    id = 303
    username = None
    first_name = "T"
    last_name = None


class FakeMessage:
    def __init__(self, raise_on_edit: bool = False):
        self.raise_on_edit = raise_on_edit
        self.edited = None

    async def edit_text(self, text):
        if self.raise_on_edit:
            raise TelegramAPIError("editMessageText", "message is not modified")
        self.edited = text


class FakeCallback:
    def __init__(self, message: FakeMessage, rating: int = 3):
        self.message = message
        self.data = f"{CALLBACK_PREFIX}:{rating}"
        self.from_user = _FromUser()
        self.answers = []

    async def answer(self, text=None, **kwargs):
        self.answers.append(text)


class StatsCallback:
    def __init__(self, data: str, user_id: int = 42):
        self.data = data
        self.from_user = _FromUser()
        self.from_user.id = user_id
        self.answers = []
        self.message = None

    async def answer(self, text=None, **kwargs):
        self.answers.append(text)


async def test_callback_answered_when_edit_succeeds(uow):
    message = FakeMessage()
    callback = FakeCallback(message, rating=4)

    await health_rating(callback, uow)

    assert message.edited is not None
    assert "4/5" in message.edited
    assert callback.answers == [None]


async def test_callback_answered_even_when_edit_fails(uow):
    """Bug 12: if edit_text raises (repeat tap / inaccessible message),
    callback.answer() must still run so the user doesn't get a stuck spinner."""
    message = FakeMessage(raise_on_edit=True)
    callback = FakeCallback(message, rating=3)

    await health_rating(callback, uow)

    assert message.edited is None
    assert callback.answers == [None]


async def test_stats_period_switch_rejected_for_foreign_user(uow):
    """A regular user must not be able to switch the period of another user."""
    from app.config import get_settings

    foreign_caller = get_settings().admin_id + 1
    callback = StatsCallback(
        data=f"{STATS_PERIOD_PREFIX}:999:14",
        user_id=foreign_caller,
    )

    await stats_callback(callback, uow)

    assert callback.answers == ["Недостаточно прав"]


async def test_stats_period_switch_own_user_passes_guard(uow):
    """A regular user may switch the period of their own chart; the guard
    must not reject it (the flow then reaches the data/not-found branch)."""
    from app.config import get_settings

    own_id = get_settings().admin_id + 1
    callback = StatsCallback(data=f"{STATS_PERIOD_PREFIX}:{own_id}:14", user_id=own_id)

    await stats_callback(callback, uow)

    assert callback.answers != ["Недостаточно прав"]
