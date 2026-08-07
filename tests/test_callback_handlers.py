import pytest
from aiogram.exceptions import TelegramAPIError

from app.telegram.callback_handlers import health_rating
from app.telegram.health_poll import CALLBACK_PREFIX

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
