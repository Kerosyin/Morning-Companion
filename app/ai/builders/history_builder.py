from __future__ import annotations

from collections.abc import Iterable

from app.db.models.message import Message


class HistoryBuilder:
    """
    Converts stored messages into OpenAI/OpenRouter chat format.
    """

    MAX_MESSAGES = 20

    @classmethod
    def build(
        cls,
        history: Iterable[Message],
    ) -> list[dict[str, str]]:
        """
        Converts the conversation history into LLM messages.
        """

        history = list(history)

        messages: list[dict[str, str]] = []

        for message in history[-cls.MAX_MESSAGES:]:

            if not message.text:
                continue

            role = message.role.value.lower()

            if role not in ("user", "assistant", "system"):
                continue

            messages.append(
                {
                    "role": role,
                    "content": message.text.strip(),
                }
            )

        return messages
