"""
Regression guards for prompt-injection hardening.

These do NOT test the LLM itself (that needs a live model). They only
assert that the protective wording stays in the prompts — so a careless
edit cannot silently remove the mitigation.
"""

from app.ai.memory_extractor import MemoryExtractor
from app.ai.prompts import SYSTEM_PROMPT


def test_system_prompt_treats_user_text_as_data():
    lower = SYSTEM_PROMPT.lower()
    assert "данные" in lower
    assert "инструкции" in lower


def test_system_prompt_forbids_disclosing_prompt():
    assert "промпт" in SYSTEM_PROMPT.lower()


def test_system_prompt_declares_rules_immutable():
    lower = SYSTEM_PROMPT.lower()
    assert "неизменны" in lower or "переопределен" in lower


def test_memory_extractor_rejects_instructions():
    lower = MemoryExtractor.SYSTEM_PROMPT.lower()
    assert "instruction" in lower
    assert "never extract" in lower
