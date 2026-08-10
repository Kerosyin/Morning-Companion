from __future__ import annotations

import io
import logging
from datetime import date, timedelta

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

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    fig.patch.set_facecolor("white")

    _draw_weekend_bands(ax, dates)
    ax.fill_between(
        dates, ratings, 0.5, alpha=0.12, color=_LINE_COLOR, zorder=1
    )
    ax.plot(dates, ratings, color=_LINE_COLOR, linewidth=2.5, zorder=3)
    ax.scatter(
        dates,
        ratings,
        c=[_RATING_COLORS.get(r, _LINE_COLOR) for r in ratings],
        s=90,
        zorder=4,
        edgecolors="white",
        linewidth=1.5,
    )
    _draw_average_line(ax, dates, average)

    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.set_title(
        f"Самочувствие за {len(checkins)} дн.",
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


def _draw_weekend_bands(ax, dates: list[date]) -> None:
    for d in dates:
        if d.weekday() >= 5:
            ax.axvspan(
                d - timedelta(hours=12),
                d + timedelta(hours=12),
                color=_WEEKEND_COLOR,
                zorder=0,
            )


def _draw_average_line(ax, dates: list[date], average: float) -> None:
    ax.axhline(
        y=average,
        color=_AVG_COLOR,
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        zorder=2,
    )
    ax.text(
        dates[-1],
        average + 0.2,
        f"Среднее {average:.1f}",
        color=_AVG_COLOR,
        fontsize=9,
        ha="right",
        va="bottom",
    )
