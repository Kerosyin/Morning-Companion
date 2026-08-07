from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.models import AIResponse, ConversationContext


class AIProvider(ABC):
    """
    Base interface for every LLM provider.
    """

    @abstractmethod
    async def chat(
        self,
        context: ConversationContext,
    ) -> AIResponse:
        """
        Full conversation with memory and history.
        """
        raise NotImplementedError

    @abstractmethod
    async def simple_chat(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Small one-shot request.

        Used by auxiliary pipelines (e.g. MemoryExtractor,
        CriticalEventDetector) that do not need the full
        ConversationContext.
        """
        raise NotImplementedError
