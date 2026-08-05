from __future__ import annotations

import json
import logging

from app.ai.provider import AIProvider

logger = logging.getLogger(__name__)


class AIReminderProvider:
    """
    Generates the day's reminder texts with an LLM once per morning.

    Instead of hitting the model every 15 minutes, the whole set of
    reminders is generated in a single request and then reused all day.
    """

    SYSTEM_PROMPT = """
Generate 12 short, friendly morning reminder messages for a Telegram bot.

Each message must be slightly more insistent than the previous one.

Rules:

- Each message is a single sentence.
- Friendly tone, no markdown, no emojis overload.
- The last message should warn about notifying the admin.

Return ONLY valid JSON, an array of exactly 12 strings:

[
    "...",
    "..."
]
"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def generate(self) -> list[str]:

        response = await self.provider.simple_chat(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt="Generate today's reminders.",
        )

        try:
            raw = json.loads(response)
        except Exception:
            logger.warning("AI reminder provider returned invalid JSON.")
            return []

        if not isinstance(raw, list):
            return []

        return [
            str(item).strip()
            for item in raw
            if isinstance(item, str) and item.strip()
        ]