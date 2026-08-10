from datetime import date, timedelta

from app.services.health_chart import (
    _period_bounds,
    _series_with_gaps,
    _tick_dates,
    render_health_chart,
)
from app.services.health_check_service import HealthCheckService
from app.telegram.stats_keyboard import (
    build_period_keyboard,
    build_user_list_keyboard,
    parse_stats_callback,
)


class _FakeUser:
    def __init__(self, telegram_id, first_name=None, username=None):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.username = username


class _FakeCheckin:
    def __init__(self, d, rating):
        self.date = d
        self.rating = rating


# ── chart rendering ──────────────────────────────────────────────


def test_render_chart_returns_png_bytes():
    today = date.today()
    checkins = [
        _FakeCheckin(today - timedelta(days=2), 3),
        _FakeCheckin(today - timedelta(days=1), 4),
        _FakeCheckin(today, 5),
    ]
    png = render_health_chart(checkins, days=3)
    assert png is not None
    assert isinstance(png, bytes)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_chart_empty_returns_none():
    assert render_health_chart([], days=7) is None


def test_render_chart_single_point():
    checkins = [_FakeCheckin(date.today(), 4)]
    png = render_health_chart(checkins, days=1)
    assert png is not None


def test_chart_period_bounds_use_selected_days():
    end = date(2026, 8, 10)
    start, period_end = _period_bounds(
        [end - timedelta(days=1)],
        days=14,
        end_date=end,
    )
    assert start == date(2026, 7, 28)
    assert period_end == end


def test_chart_ticks_are_unique_for_long_period():
    start = date(2026, 7, 12)
    end = date(2026, 8, 10)
    ticks = _tick_dates(start, end, days=30)
    labels = [f"{tick:%d.%m}" for tick in ticks]
    assert len(labels) == len(set(labels))
    assert ticks[0] == start
    assert ticks[-1] == end


def test_chart_ticks_sparse_for_three_month_period():
    start = date(2026, 5, 12)
    end = date(2026, 8, 10)
    ticks = _tick_dates(start, end, days=90)
    labels = [f"{tick:%d.%m}" for tick in ticks]
    assert len(labels) == len(set(labels))
    assert ticks[0] == start
    assert ticks[-1] == end
    assert len(ticks) <= 20


def test_chart_series_breaks_line_on_missing_days():
    start = date(2026, 8, 1)
    end = date(2026, 8, 3)
    dates, ratings = _series_with_gaps(
        [
            _FakeCheckin(date(2026, 8, 1), 4),
            _FakeCheckin(date(2026, 8, 3), 5),
        ],
        start,
        end,
    )
    assert dates == [date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3)]
    assert ratings[0] == 4
    assert ratings[1] != ratings[1]
    assert ratings[2] == 5


# ── HealthCheckService.chart ────────────────────────────────────


async def _make_user(uow) -> int:
    async with uow:
        user = await uow.users.get_or_create(
            999, defaults={"username": "tester", "first_name": "T"}
        )
        await uow.commit()
        return user.id


async def test_service_chart_returns_png(uow):
    user_id = await _make_user(uow)
    async with uow:
        await uow.health_checkins.create_or_update(user_id, date.today(), 4)
        await uow.commit()

    service = HealthCheckService(days=7)
    async with uow:
        png = await service.chart(uow, user_id)

    assert png is not None
    assert png[:4] == b"\x89PNG"


async def test_service_chart_no_data_returns_none(uow):
    user_id = await _make_user(uow)
    service = HealthCheckService(days=7)
    async with uow:
        png = await service.chart(uow, user_id)
    assert png is None


# ── keyboards ───────────────────────────────────────────────────


def test_user_list_keyboard_has_button_per_user():
    users = [
        _FakeUser(111, first_name="Иван"),
        _FakeUser(222, username="maria"),
    ]
    kb = build_user_list_keyboard(users)
    texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert "Иван" in texts
    assert "maria" in texts


def test_user_list_keyboard_empty():
    kb = build_user_list_keyboard([])
    assert kb.inline_keyboard == []


def test_period_keyboard_marks_current():
    kb = build_period_keyboard(telegram_id=123, current_days=14)
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    active = [b for b in buttons if b.text.startswith("•")]
    assert len(active) == 1
    assert "14" in active[0].text


def test_period_keyboard_callback_data_format():
    kb = build_period_keyboard(telegram_id=123456, current_days=7)
    for row in kb.inline_keyboard:
        for btn in row:
            assert btn.callback_data.startswith("stats:p:123456:")


# ── callback parsing ────────────────────────────────────────────


def test_parse_user_callback():
    result = parse_stats_callback("stats:u:164861636")
    assert result == ("user", 164861636, 7)


def test_parse_period_callback():
    result = parse_stats_callback("stats:p:164861636:14")
    assert result == ("period", 164861636, 14)


def test_parse_invalid_callback():
    assert parse_stats_callback("health_check:3") is None
    assert parse_stats_callback("stats:x:1") is None
    assert parse_stats_callback("stats:u:") is None
    assert parse_stats_callback("") is None
