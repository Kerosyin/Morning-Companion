from __future__ import annotations

from app.ai.models import AIResponse, ConversationContext
from app.ai.provider import AIProvider


class ConversationService:
    """
    Responsible only for communicating with the LLM.
    """

    def __init__(
        self,
        provider: AIProvider,
    ) -> None:

        self.provider = provider

    async def reply(
        self,
        context: ConversationContext,
    ) -> AIResponse:
        """
        Generates an AI response using the configured provider.
        """

        return await self.provider.chat(context)
