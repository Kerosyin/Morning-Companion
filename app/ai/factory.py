from app.ai.openrouter import OpenRouterProvider
from app.ai.provider import AIProvider


_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """
    Factory function to get the configured AI provider using a singleton pattern.
    """
    global _provider

    if _provider is None:
        _provider = OpenRouterProvider()

    return _provider
