from app.ai.prompts import SYSTEM_PROMPT


class PromptBuilder:
    """Builds the system prompt."""

    @staticmethod
    def build() -> str:
        return SYSTEM_PROMPT
