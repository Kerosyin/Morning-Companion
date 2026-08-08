import pytest

from app.ai.critical_event_detector import CriticalEvent
from app.db.models.critical_event import CriticalSeverity
from app.services.dialog_service import DialogResult
from app.telegram import handlers

pytestmark = pytest.mark.asyncio


class _FromUser:
    id = 42
    username = None
    first_name = "T"
    last_name = None


class _FakeBot:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_message(self, chat_id, text=None, **kwargs):
        self.sent.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": kwargs.get("reply_markup"),
            }
        )


class _FakeMessage:
    def __init__(self, text: str = "привет") -> None:
        self.text = text
        self.content_type = "text"
        self.from_user = _FromUser()
        self.bot = _FakeBot()
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


class _FakeDialogService:
    def __init__(self, result: DialogResult) -> None:
        self._result = result

    async def process_message(self, uow, message):
        return self._result


def _patch_container(monkeypatch, result: DialogResult) -> None:
    container = type(
        "C",
        (),
        {"dialog_service": lambda self: _FakeDialogService(result)},
    )()
    monkeypatch.setattr(handlers, "get_container", lambda: container)


async def test_health_poll_sent_after_reply(uow, monkeypatch):
    """On a first non-critical message the bot replies, then sends the
    health poll as a separate message with the rating keyboard."""
    _patch_container(
        monkeypatch,
        DialogResult(reply="ответ бота", health_poll_pending=True),
    )
    message = _FakeMessage()

    await handlers.process_user_message(message, uow)

    assert message.answers == ["ответ бота"]
    assert len(message.bot.sent) == 1
    assert message.bot.sent[0]["reply_markup"] is not None


async def test_health_poll_suppressed_on_critical_event(uow, monkeypatch):
    """On a first critical message the health poll must be suppressed; only
    the admin notification is sent (no rating keyboard)."""
    event = CriticalEvent(
        severity=CriticalSeverity.HIGH,
        event_type="fire",
        description="пожар",
    )
    _patch_container(
        monkeypatch,
        DialogResult(
            reply="держись",
            critical_event=event,
            health_poll_pending=True,
        ),
    )
    message = _FakeMessage()

    await handlers.process_user_message(message, uow)

    assert message.answers == ["держись"]
    # Only the admin notification is sent, and without a rating keyboard.
    assert len(message.bot.sent) == 1
    assert message.bot.sent[0]["reply_markup"] is None
