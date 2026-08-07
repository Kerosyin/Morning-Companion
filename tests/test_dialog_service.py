import pytest
from sqlalchemy import select

from app.ai.models import AIResponse, ConversationContext
from app.ai.provider import AIProvider
from app.db.models import Message
from app.services.dialog_service import AI_UNAVAILABLE_REPLY, DialogService

pytestmark = pytest.mark.asyncio


class FailingProvider(AIProvider):
    async def chat(self, context: ConversationContext):
        raise RuntimeError("provider down")

    async def simple_chat(self, system_prompt: str, user_prompt: str):
        raise RuntimeError("provider down")


class SpyProvider(AIProvider):
    """Records the context handed to chat() so a test can assert on it."""

    def __init__(self, reply: str = "ок"):
        self.reply = reply
        self.last_context: ConversationContext | None = None

    async def chat(self, context: ConversationContext) -> AIResponse:
        self.last_context = context
        return AIResponse(reply=self.reply)

    async def simple_chat(self, system_prompt: str, user_prompt: str):
        return "[]"


class TelegramMessageStub:
    class _FromUser:
        id = 42
        username = None
        first_name = "T"
        last_name = None

    from_user = _FromUser()

    def __init__(self, text: str = "привет"):
        self.text = text


async def test_dialog_service_fallback_when_ai_fails(uow):
    service = DialogService(provider=FailingProvider())

    result = await service.process_message(uow, TelegramMessageStub())

    assert result.reply == AI_UNAVAILABLE_REPLY


async def test_user_message_persisted_when_ai_fails(uow):
    """Bug 1: even when the AI provider fails, the user's message and the
    first_message_at flag must be committed (not silently dropped)."""
    service = DialogService(provider=FailingProvider())
    stub = TelegramMessageStub(text="сохрани меня")

    result = await service.process_message(uow, stub)

    assert result.reply == AI_UNAVAILABLE_REPLY

    async with uow:
        user = await uow.users.get_by_telegram_id(stub.from_user.id)
        assert user is not None

        messages = (
            await uow.session.execute(
                select(Message).where(Message.user_id == user.id)
            )
        ).scalars().all()
        assert len(messages) == 1
        assert messages[0].text == "сохрани меня"

        activity = await uow.daily_activity.get_or_create_today(user.id)
        assert activity.first_message_at is not None


async def test_current_message_not_duplicated_in_llm_context(uow):
    """Bug 3: the user's current message must not be both saved-then-read as
    history and appended again by ContextBuilder (would reach the LLM twice).
    History is fetched before saving, so it must not contain the message."""
    provider = SpyProvider()
    service = DialogService(provider=provider)
    stub = TelegramMessageStub(text="совершенно-уникальная-фраза-xyz")

    await service.process_message(uow, stub)

    assert provider.last_context is not None
    history_texts = [
        m.text
        for m in provider.last_context.history
        if m.role.value == "user"
    ]
    assert stub.text not in history_texts
    assert provider.last_context.message == stub.text


async def test_long_message_truncated_for_llm_but_persisted_full(uow):
    """Security: a huge message is capped before reaching the LLM (token-burn
    / abuse protection), while the full text is still stored in the database."""
    from app.config import get_settings

    max_len = get_settings().message_max_length
    long_text = "а" * (max_len + 500)

    provider = SpyProvider()
    service = DialogService(provider=provider)
    stub = TelegramMessageStub(text=long_text)

    await service.process_message(uow, stub)

    assert provider.last_context is not None
    assert len(provider.last_context.message) == max_len

    async with uow:
        user = await uow.users.get_by_telegram_id(stub.from_user.id)
        messages = (
            await uow.session.execute(
                select(Message).where(Message.user_id == user.id)
            )
        ).scalars().all()
    assert messages[0].text == long_text
