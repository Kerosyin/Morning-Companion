import asyncio
import logging

import aiohttp

from app.ai.builders.context_builder import ContextBuilder
from app.ai.models import AIResponse, ConversationContext
from app.ai.provider import AIProvider
from app.config import get_settings

logger = logging.getLogger("morning_companion")


class OpenRouterProvider(AIProvider):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.model = settings.model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.proxy = settings.proxy
        self.max_retries = 3

    async def chat(self, context: ConversationContext) -> AIResponse:
        """
        Generates a response using the OpenRouter API, with the context
        pre-processed by the builder pipeline.
        """
        messages = ContextBuilder.build(context)
        reply_text = await self._request(messages)
        return AIResponse(reply=reply_text)

    async def simple_chat(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Sends a single-turn completion and returns the raw model text.
        Used by auxiliary pipelines that do not need the full
        ConversationContext (e.g. memory extraction, summaries).
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self._request(messages)

    async def _request(self, messages: list[dict]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "messages": messages}

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                logger.info(
                    "Запрос к OpenRouter (model=%s, attempt=%d/%d)",
                    self.model,
                    attempt + 1,
                    self.max_retries,
                )
                try:
                    async with session.post(
                        self.api_url, headers=headers, json=payload, proxy=self.proxy
                    ) as response:
                        if response.status not in (429, 500, 502, 503, 504):
                            response.raise_for_status()
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                        logger.warning(
                            "OpenRouter вернул %s, повтор через %ds",
                            response.status,
                            2**attempt,
                        )
                        await asyncio.sleep(2**attempt)
                except aiohttp.ClientError as exc:
                    logger.warning(
                        "Сбой соединения с OpenRouter (%s), повтор через %ds",
                        exc,
                        2**attempt,
                    )
                    await asyncio.sleep(2**attempt)
            raise RuntimeError(
                f"OpenRouter не ответил после {self.max_retries} попыток"
            )
