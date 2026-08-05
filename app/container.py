from __future__ import annotations

from app.ai.provider import AIProvider
from app.services.dialog_service import DialogService

_default_container: "Container | None" = None


class Container:
    """Lightweight dependency container.

    Builds the object graph once and allows swapping the AI provider,
    which makes the services testable.
    """

    def __init__(self) -> None:
        self._provider: AIProvider | None = None
        self._dialog_service: DialogService | None = None

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            from app.ai.openrouter import OpenRouterProvider

            self._provider = OpenRouterProvider()
        return self._provider

    def set_provider(self, provider: AIProvider) -> None:
        self._provider = provider
        self._dialog_service = None

    def dialog_service(self) -> DialogService:
        if self._dialog_service is None:
            self._dialog_service = DialogService(provider=self.provider)
        return self._dialog_service


def get_container() -> Container:
    global _default_container
    if _default_container is None:
        _default_container = Container()
    return _default_container


def reset_container() -> None:
    """Reset the default container (used mainly in tests)."""
    global _default_container
    _default_container = None
