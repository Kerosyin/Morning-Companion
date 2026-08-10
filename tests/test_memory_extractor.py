import pytest

from app.ai.memory_extractor import MemoryExtractor
from app.ai.models import ConversationContext
from app.ai.provider import AIProvider

pytestmark = pytest.mark.asyncio


class FakeProvider(AIProvider):
    def __init__(self, response: str):
        self.response = response

    async def chat(self, context: ConversationContext):
        raise NotImplementedError

    async def simple_chat(self, system_prompt: str, user_prompt: str):
        return self.response


class FakeUser:
    id = 1


def make_context(message: str) -> ConversationContext:
    return ConversationContext(
        user=FakeUser(), history=[], memories=[], message=message
    )


async def test_extracts_memories_from_valid_json():
    extractor = MemoryExtractor(
        FakeProvider('[{"category":"pets","key":"dog","value":"Rex"}]')
    )

    result = await extractor.extract(make_context("моя собака Рекс"))

    assert len(result) == 1
    assert result[0].category == "pets"
    assert result[0].key == "dog"
    assert result[0].value == "Rex"


async def test_invalid_json_returns_empty():
    extractor = MemoryExtractor(FakeProvider("это не json"))

    assert await extractor.extract(make_context("x")) == []


async def test_non_list_json_returns_empty():
    """Bug 13: a scalar/object JSON value must not crash with TypeError
    inside the for-loop; it must return an empty list."""
    for payload in ("null", "{}", "42", "\"строка\""):
        extractor = MemoryExtractor(FakeProvider(payload))
        assert await extractor.extract(make_context("x")) == []


async def test_normalizes_and_filters_memory_fields():
    extractor = MemoryExtractor(
        FakeProvider(
            """[
                {"category": " pets ", "key": " dog ", "value": " Rex "},
                {"category": "", "key": "empty-value", "value": ""},
                ["not", "a", "dict"],
                {"key": "long", "value": "%s"}
            ]"""
            % ("x" * 250)
        )
    )

    result = await extractor.extract(make_context("x"))

    assert len(result) == 2
    assert result[0].category == "pets"
    assert result[0].key == "dog"
    assert result[0].value == "Rex"
    assert result[1].category == "general"
    assert result[1].key == "long"
    assert len(result[1].value) == 200
