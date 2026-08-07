from dataclasses import dataclass
from typing import List

from app.db.models import Memory, Message, User


@dataclass
class AIResponse:
    """
    Represents a structured response from an AI provider.
    """
    reply: str


@dataclass
class ConversationContext:
    """
    Represents the full context provided to an AI provider for generating a response.
    """
    user: User
    history: List[Message]
    memories: List[Memory]
    message: str
