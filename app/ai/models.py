from dataclasses import dataclass, field
from typing import List, Optional

from app.db.models import Memory, Message, User


@dataclass
class AIResponse:
    """
    Represents a structured response from an AI provider.
    """
    reply: str
    memory_updates: list = field(default_factory=list)
    mood: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class ConversationContext:
    """
    Represents the full context provided to an AI provider for generating a response.
    """
    user: User
    history: List[Message]
    memories: List[Memory]
    message: str
