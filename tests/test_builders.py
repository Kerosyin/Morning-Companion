from app.ai.builders.history_builder import HistoryBuilder
from app.ai.builders.memory_builder import MemoryBuilder
from app.db.models import Memory, Message
from app.db.models.message import MessageRole


class FakeMemory(Memory):
    """Memory subclass that allows ad-hoc construction without DB."""

    def __init__(self, category, key, value):
        self.category = category
        self.key = key
        self.value = value


class FakeMessage(Message):
    """Message subclass that allows ad-hoc construction without DB."""

    def __init__(self, role, text):
        self.role = role
        self.text = text


def test_history_builder_filters_empty_text():
    """Empty (falsy) messages must not reach the LLM.

    Note: whitespace-only filtering happens earlier in HistoryManager.prepare;
    HistoryBuilder is called downstream on already-cleaned history."""
    history = [
        FakeMessage(MessageRole.USER, "привет"),
        FakeMessage(MessageRole.ASSISTANT, ""),
        FakeMessage(MessageRole.ASSISTANT, "как дела?"),
    ]

    messages = HistoryBuilder.build(history)

    assert [m["content"] for m in messages] == ["привет", "как дела?"]
    assert all(m["role"] in ("user", "assistant") for m in messages)


def test_history_builder_caps_to_max_messages():
    history = [
        FakeMessage(MessageRole.USER, f"msg-{i}") for i in range(30)
    ]

    messages = HistoryBuilder.build(history)

    assert len(messages) == HistoryBuilder.MAX_MESSAGES
    assert messages[0]["content"] == "msg-10"
    assert messages[-1]["content"] == "msg-29"


def test_memory_builder_groups_by_category():
    """Bug 9: facts must be grouped by their stored category column."""
    memories = [
        FakeMemory("pets", "dog", "Rex"),
        FakeMemory("pets", "cat", "Murka"),
        FakeMemory("work", "job", "engineer"),
    ]

    block = MemoryBuilder.build(memories)

    assert "Pets:" in block
    assert "Work:" in block
    pets_idx = block.index("Pets:")
    work_idx = block.index("Work:")
    assert pets_idx < work_idx  # sorted alphabetically
    assert "dog: Rex" in block
    assert "cat: Murka" in block
    assert "job: engineer" in block


def test_memory_builder_empty_returns_empty_string():
    assert MemoryBuilder.build([]) == ""
