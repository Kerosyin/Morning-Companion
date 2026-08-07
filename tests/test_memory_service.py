import pytest
from sqlalchemy import select

from app.db.models import Memory

pytestmark = pytest.mark.asyncio


async def test_set_memory_persists_category(uow):
    """Bug 9: category must be stored in its own column, not glued into the
    key as 'category:key'."""
    async with uow:
        user = await uow.users.get_or_create(
            555, defaults={"first_name": "T"}
        )
        await uow.memories.set_memory(
            user=user, key="dog", value="Rex", category="pets"
        )
        await uow.commit()

    async with uow:
        mem = await uow.memories.get_memory(user, "dog")
        assert mem is not None
        assert mem.category == "pets"
        assert mem.key == "dog"

        prefixed = (
            await uow.session.execute(
                select(Memory).where(Memory.key == "pets:dog")
            )
        ).scalars().first()
        assert prefixed is None


async def test_set_memory_default_category(uow):
    async with uow:
        user = await uow.users.get_or_create(
            556, defaults={"first_name": "T"}
        )
        await uow.memories.set_memory(
            user=user, key="city", value="Moscow"
        )
        await uow.commit()

    async with uow:
        mem = await uow.memories.get_memory(user, "city")
        assert mem is not None
        assert mem.category == "general"


async def test_set_memory_updates_value_and_category(uow):
    async with uow:
        user = await uow.users.get_or_create(
            557, defaults={"first_name": "T"}
        )
        await uow.memories.set_memory(
            user=user, key="dog", value="Rex", category="pets"
        )
        await uow.memories.set_memory(
            user=user, key="dog", value="Balto", category="pets"
        )
        await uow.commit()

    async with uow:
        mem = await uow.memories.get_memory(user, "dog")
        assert mem is not None
        assert mem.value == "Balto"
        assert mem.category == "pets"
