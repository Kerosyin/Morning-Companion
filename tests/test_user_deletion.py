import pytest

pytestmark = pytest.mark.asyncio


async def test_delete_by_telegram_id_removes_user_grant_and_notifications(uow):
    async with uow:
        await uow.users.get_or_create(
            123,
            defaults={"username": None, "first_name": "Test", "last_name": None},
        )
        await uow.access_grants.grant(123, granted_by=1)
        await uow.notifications.get_or_create(
            kind="morning",
            dedupe_key="delete-test",
            chat_id=123,
            text="pending",
        )
        await uow.commit()

    async with uow:
        assert await uow.users.delete_by_telegram_id(123) is True
        await uow.access_grants.revoke(123)
        await uow.notifications.delete_by_chat_id(123)
        await uow.commit()

    async with uow:
        assert await uow.users.get_by_telegram_id(123) is None
        assert await uow.access_grants.is_granted(123) is False
        assert await uow.notifications.get_by_key("morning", "delete-test") is None
