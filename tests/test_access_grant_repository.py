import pytest

pytestmark = pytest.mark.asyncio


async def test_grant_is_idempotent_and_persistent(uow):
    async with uow:
        assert await uow.access_grants.grant(1001, granted_by=1) is True
        assert await uow.access_grants.grant(1001, granted_by=1) is False
        await uow.commit()

    async with uow:
        assert await uow.access_grants.is_granted(1001) is True
        grants = await uow.access_grants.list_all()

    assert [grant.telegram_id for grant in grants] == [1001]


async def test_revoke_reports_whether_a_grant_existed(uow):
    async with uow:
        assert await uow.access_grants.revoke(1001) is False
        assert await uow.access_grants.grant(1001, granted_by=1) is True
        assert await uow.access_grants.revoke(1001) is True
        await uow.commit()

    async with uow:
        assert await uow.access_grants.is_granted(1001) is False
