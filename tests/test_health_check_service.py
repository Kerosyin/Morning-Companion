from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.db.models import HealthCheckin
from app.services.health_check_service import HealthCheckService

pytestmark = pytest.mark.asyncio


async def make_user(uow) -> int:
    async with uow:
        user = await uow.users.get_or_create(
            999, defaults={"username": "tester", "first_name": "T"}
        )
        await uow.commit()
        return user.id


async def test_save_and_dedup_same_day(uow):
    user_id = await make_user(uow)

    async with uow:
        first = await uow.health_checkins.create_or_update(
            user_id, date.today(), 3
        )
        second = await uow.health_checkins.create_or_update(
            user_id, date.today(), 5
        )
        result = await uow.session.execute(select(HealthCheckin))
        checkins = result.scalars().all()
        await uow.commit()

    assert first.id == second.id
    assert len(checkins) == 1
    assert checkins[0].rating == 5


async def test_trend_builds_report(uow):
    user_id = await make_user(uow)

    async with uow:
        for offset, rating in ((1, 4), (2, 3), (3, 5)):
            await uow.health_checkins.create_or_update(
                user_id, date.today() - timedelta(days=offset), rating
            )
        await uow.commit()

    service = HealthCheckService(days=7)
    async with uow:
        report = await service.trend(uow, user_id)

    assert "среднее 4.0/5" in report
    assert "за последние 7 дн." in report
    assert "записей 3" in report
    assert "3" in report
    assert "5" in report


async def test_trend_empty(uow):
    user_id = await make_user(uow)

    async with uow:
        report = await HealthCheckService().trend(uow, user_id)

    assert "нет данных" in report


async def test_trend_bar_reflects_rating(uow):
    """Bug 2: the bar must mirror the rating (3 filled + 2 empty for rating 3),
    not always render as a fully filled bar."""
    user_id = await make_user(uow)

    async with uow:
        await uow.health_checkins.create_or_update(user_id, date.today(), 3)
        await uow.commit()

    service = HealthCheckService(days=7)
    async with uow:
        report = await service.trend(uow, user_id)

    assert "███░░" in report
    assert "█████" not in report


async def test_trend_bar_full_for_rating_5(uow):
    """Bug 2: rating 5 renders a fully filled bar with no empty blocks."""
    user_id = await make_user(uow)

    async with uow:
        await uow.health_checkins.create_or_update(user_id, date.today(), 5)
        await uow.commit()

    service = HealthCheckService(days=7)
    async with uow:
        report = await service.trend(uow, user_id)

    assert "█████" in report
    assert "░" not in report

