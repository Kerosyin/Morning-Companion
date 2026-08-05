from app.ai.provider import AIProvider
from app.ai.openrouter import OpenRouterProvider
from app.config import get_settings

settings = get_settings()


def get_ai_provider() -> AIProvider:
    """
    Factory function to get the configured AI provider.
    """
    provider_name = settings.ai_provider.lower()

    if provider_name == "openrouter":
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            model=settings.model,
        )
    # In the future, we can add other providers like "ollama", "glm", etc.
    # elif provider_name == "ollama":
    #     return OllamaProvider(...)

    raise ValueError(f"Unknown AI provider: {provider_name}")


# You can also have a single instance if you prefer
ai_provider_instance = get_ai_provider()
