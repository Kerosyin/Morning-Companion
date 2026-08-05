from __future__ import annotations

from app.ai.provider import AIProvider


class ReminderGenerationService:
    """
    Generates a set of reminder messages for one day.
    """

    SYSTEM_PROMPT = """
Generate 12 short morning reminder messages.

Rules:

- Friendly.
- Natural.
- Each message should be slightly more persistent.
- No markdown.
- Maximum 20 words.
- Return JSON array only.
"""

    def __init__(
        self,
        provider: AIProvider,
    ) -> None:

        self.provider = provider

    async def generate(self) -> list[str]:

        response = await self.provider.simple_chat(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt="Generate reminders.",
        )

        # Пока сделаем заглушку.
        # Следующим PR заменим на полноценный JSON parser.
        return [response]
