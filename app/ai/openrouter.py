import aiohttp

from app.ai.builders.context_builder import ContextBuilder
from app.ai.models import AIResponse, ConversationContext
from app.ai.provider import AIProvider
from app.config import get_settings


class OpenRouterProvider(AIProvider):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.model = settings.model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

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
            async with session.post(
                self.api_url, headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data["choices"][0]["message"]["content"]
