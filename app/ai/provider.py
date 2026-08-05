from typing import Protocol

from app.ai.models import ConversationContext, AIResponse


class AIProvider(Protocol):
    """
    Defines the interface for an AI provider.
    Any AI implementation must adhere to this protocol.
    """

    async def chat(
        self,
        context: ConversationContext,
    ) -> AIResponse:
        """
        Generates a response based on the given conversation context.
        """
        ...
