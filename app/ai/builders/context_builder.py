from __future__ import annotations

from app.ai.builders.history_builder import HistoryBuilder
from app.ai.builders.memory_builder import MemoryBuilder
from app.ai.builders.prompt_builder import PromptBuilder
from app.ai.models import ConversationContext


class ContextBuilder:
    """
    Builds a list of messages that will be sent to the LLM.
    """

    @classmethod
    def build(cls, context: ConversationContext) -> list[dict]:
        messages: list[dict] = []

        messages.append(
            {
                "role": "system",
                "content": PromptBuilder.build(),
            }
        )

        memory = MemoryBuilder.build(context.memories)

        if memory:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Known information about the user.\n"
                        "Use it naturally in conversation.\n\n"
                        f"{memory}"
                    ),
                }
            )

        messages.extend(
            HistoryBuilder.build(context.history)
        )

        messages.append(
            {
                "role": "user",
                "content": context.message,
            }
        )

        return messages