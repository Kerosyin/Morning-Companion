import aiohttp
from typing import List, Dict

from app.ai.models import ConversationContext, AIResponse
from app.ai.provider import AIProvider
from app.ai.prompts import SYSTEM_PROMPT
from app.config import get_settings
from app.db.models.message import MessageRole

settings = get_settings()


class OpenRouterProvider(AIProvider):
    """
    An AI provider implementation for OpenRouter.
    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    async def chat(self, context: ConversationContext) -> AIResponse:
        """
        Generates a response using the OpenRouter API.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Take last 15 messages
        history_messages = context.history[-15:]

        messages = self._build_messages(history_messages, context.message)

        payload = {
            "model": self.model,
            "messages": messages,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                reply_text = data["choices"][0]["message"]["content"]
                return AIResponse(reply=reply_text)

    def _build_messages(self, history: List[Dict], user_message: str) -> List[Dict]:
        """
        Builds the list of messages for the API call.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history:
            messages.append({"role": msg.role.value, "content": msg.text})

        messages.append({"role": MessageRole.USER.value, "content": user_message})
        return messages
