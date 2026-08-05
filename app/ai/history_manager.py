from __future__ import annotations

from app.db.models.message import Message


class HistoryManager:
    """
    Prepares conversation history for the LLM.
    """

    MAX_MESSAGES = 20

    def prepare(
        self,
        history: list[Message],
    ) -> list[Message]:

        cleaned: list[Message] = []

        for message in history:

            if not message.text:
                continue

            text = message.text.strip()

            if not text:
                continue

            cleaned.append(message)

        return cleaned[-self.MAX_MESSAGES:]