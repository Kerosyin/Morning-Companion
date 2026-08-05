from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from app.db.models.memory import Memory


class MemoryBuilder:
    """
    Builds a readable memory block for the LLM.
    """

    @classmethod
    def build(
        cls,
        memories: Iterable[Memory],
    ) -> str:

        memories = list(memories)

        if not memories:
            return ""

        grouped = defaultdict(list)

        for memory in memories:
            grouped[memory.category].append(memory)

        lines: list[str] = []

        lines.append(
            "Information remembered about the user:"
        )

        for category in sorted(grouped.keys()):

            lines.append("")
            lines.append(f"{category.title()}:")

            for memory in grouped[category]:

                lines.append(
                    f"- {memory.key}: {memory.value}"
                )

        return "\n".join(lines)
