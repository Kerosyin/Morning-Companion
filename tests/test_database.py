import pytest

from app.db.uow import IUnitOfWork

pytestmark = pytest.mark.asyncio


class TestUserRepository:
    async def test_get_or_create_creates_new_user(self, uow: IUnitOfWork):
        """
        Tests that a new user is created if one doesn't exist.
        """
        async with uow:
            user = await uow.users.get_or_create(
                telegram_id=123,
                defaults={"username": "testuser", "first_name": "Test"},
            )
            await uow.commit()

            assert user.id is not None
            assert user.telegram_id == 123
            assert user.username == "testuser"

            # Verify the user is in the database
            fetched_user = await uow.users.get(user.id)
            assert fetched_user is not None
            assert fetched_user.telegram_id == 123

    async def test_get_or_create_retrieves_existing_user(self, uow: IUnitOfWork):
        """
        Tests that an existing user is retrieved without overwriting it.
        """
        # First, create the user
        async with uow:
            user = await uow.users.get_or_create(
                telegram_id=456,
                defaults={"username": "original", "first_name": "Original"},
            )
            await uow.commit()

        # Then, get_or_create the same user with updated info
        async with uow:
            fetched = await uow.users.get_or_create(
                telegram_id=456,
                defaults={"username": "updated", "first_name": "Updated"},
            )
            await uow.commit()

            assert fetched.id == user.id
            assert fetched.telegram_id == 456
            # get_or_create does not overwrite an existing user
            assert fetched.username == "original"

            # Verify the user is in the database
            db_user = await uow.users.get(user.id)
            assert db_user is not None
            assert db_user.telegram_id == 456


class TestMessageAndMemoryRepository:
    async def test_create_message_and_memory(self, uow: IUnitOfWork):
        """
        Tests creating a message and a memory linked to a user within one transaction.
        """
        async with uow:
            user = await uow.users.get_or_create(
                telegram_id=789, defaults={"first_name": "Tester"}
            )
            
            message = await uow.messages.create(
                user_id=user.id, role="user", text="Hello, world!"
            )
            
            memory = await uow.memories.set_memory(
                user=user, key="test_key", value="test_value"
            )
            
            await uow.commit()

            assert message.id is not None
            assert message.user_id == user.id
            assert memory.id is not None
            assert memory.user_id == user.id
            assert memory.value == "test_value"

            # Verify history retrieval
            history = await uow.messages.get_history(user, limit=5)
            assert len(history) == 1
            assert history[0].text == "Hello, world!"
