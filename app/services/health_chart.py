from __future__ import annotations

import io
import logging
from datetime import date, datetime, time, timedelta

logger = logging.getLogger("morning_companion")

_RATING_COLORS = {
    1: "#e74c3c",
    2: "#e67e22",
    3: "#f1c40f",
    4: "#2ecc71",
    5: "#27ae60",
}

_LINE_COLOR = "#2E86AB"
_AVG_COLOR = "#95a5a6"
_WEEKEND_COLOR = "#f0f3f5"
_GRID_COLOR = "#dcdfe1"
_TEXT_COLOR = "#2c3e50"


def render_health_chart(
    checkins: list,
    days: int,
    end_date: date | None = None,
) -> bytes | None:
    """Render a well-being trend chart as PNG bytes.

    Returns *None* when *checkins* is empty.
    """
    if not checkins:
        return None

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    dates: list[date] = [c.date for c in checkins]
    ratings: list[int] = [c.rating for c in checkins]
    average = sum(ratings) / len(ratings)
    period_days = max(days, 1)
    period_start, period_end = _period_bounds(dates, period_days, end_date)
    series_dates, series_ratings = _series_with_gaps(
        checkins,
        period_start,
        period_end,
    )

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    fig.patch.set_facecolor("white")

    _draw_weekend_bands(ax, period_start, period_end)
    ax.fill_between(
        series_dates,
        series_ratings,
        0.5,
        alpha=0.12,
        color=_LINE_COLOR,
        zorder=1,
    )
    ax.plot(series_dates, series_ratings, color=_LINE_COLOR, linewidth=2.5, zorder=3)
    ax.scatter(
        dates,
        ratings,
        c=[_RATING_COLORS.get(r, _LINE_COLOR) for r in ratings],
        s=90,
        zorder=4,
        edgecolors="white",
        linewidth=1.5,
    )
    _draw_average_line(ax, period_end, average)

    ax.set_xlim(
        _day_start(period_start) - timedelta(hours=12),
        _day_start(period_end) + timedelta(hours=12),
    )
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_xticks(_tick_dates(period_start, period_end, period_days))
    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.set_title(
        f"Самочувствие за {period_days} дн.",
        fontsize=15,
        fontweight="bold",
        pad=12,
        color=_TEXT_COLOR,
    )

    ax.grid(axis="y", alpha=0.3, linestyle="-", color=_GRID_COLOR)
    ax.set_axisbelow(True)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(_GRID_COLOR)
    ax.spines["bottom"].set_color(_GRID_COLOR)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _period_bounds(
    dates: list[date],
    days: int,
    end_date: date | None = None,
) -> tuple[date, date]:
    period_end = end_date or date.today()
    if dates:
        period_end = max(period_end, max(dates))
    period_start = period_end - timedelta(days=days - 1)
    return period_start, period_end


def _tick_dates(start: date, end: date, days: int) -> list[date]:
    interval = 1 if days <= 14 else 3 if days <= 60 else 7
    ticks = []
    current = start
    while current <= end:
        ticks.append(current)
        current += timedelta(days=interval)
    if ticks[-1] != end:
        ticks.append(end)
    return ticks


def _series_with_gaps(
    checkins: list,
    start: date,
    end: date,
) -> tuple[list[date], list[float]]:
    ratings_by_date = {checkin.date: checkin.rating for checkin in checkins}
    dates = []
    ratings = []
    current = start
    while current <= end:
        dates.append(current)
        ratings.append(float(ratings_by_date.get(current, "nan")))
        current += timedelta(days=1)
    return dates, ratings


def _draw_weekend_bands(ax, start: date, end: date) -> None:
    d = start
    while d <= end:
        if d.weekday() >= 5:
            day_start = _day_start(d)
            ax.axvspan(
                day_start - timedelta(hours=12),
                day_start + timedelta(hours=12),
                color=_WEEKEND_COLOR,
                zorder=0,
            )
        d += timedelta(days=1)


def _draw_average_line(ax, period_end: date, average: float) -> None:
    ax.axhline(
        y=average,
        color=_AVG_COLOR,
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        zorder=2,
    )
    ax.text(
        period_end,
        average + 0.2,
        f"Среднее {average:.1f}",
        color=_AVG_COLOR,
        fontsize=9,
        ha="right",
        va="bottom",
    )


def _day_start(d: date) -> datetime:
    return datetime.combine(d, time.min)
