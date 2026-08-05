import pytest

from app.ai.models import ConversationContext
from app.ai.provider import AIProvider
from app.container import get_container, reset_container
from app.services.dialog_service import AI_UNAVAILABLE_REPLY, DialogService

pytestmark = pytest.mark.asyncio


class FailingProvider(AIProvider):
    async def chat(self, context: ConversationContext):
        raise RuntimeError("provider down")

    async def simple_chat(self, system_prompt: str, user_prompt: str):
        raise RuntimeError("provider down")


async def test_dialog_service_fallback_when_ai_fails(uow):
    reset_container()
    container = get_container()
    container.set_provider(FailingProvider())

    service = DialogService(provider=container.provider)

    result = await service.process_message(uow, TelegramMessageStub())

    assert result == AI_UNAVAILABLE_REPLY


class TelegramMessageStub:
    class _FromUser:
        id = 42
        username = None
        first_name = "T"
        last_name = None

    from_user = _FromUser()
    text = "привет"
