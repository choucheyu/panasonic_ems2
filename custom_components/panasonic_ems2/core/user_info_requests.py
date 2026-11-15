"""UserGetInfo request-window helpers.

Kept Home Assistant independent so date/range behavior can be tested without HA.

The Panasonic cloud aligns every UserGetInfo window to a calendar boundary and
ignores the rest of ``from``:

* ``unit: day`` returns the month that contains ``from``, starting on day 1.
  ``from: 2026/10/17, max_num: 30`` returns 2026-10-01 .. 2026-10-30.
* ``unit: month`` returns the year that contains ``from``, starting in January.
  ``from: 2025/12/01, max_num: 12`` returns 2025-01 .. 2025-12.

``max_num`` only truncates (or pads with zeros past the end of the period), so
windows must start on the first day of a month / the first month of a year and
labels must be derived from the calendar, not from the response length.
Daily power is only retained for the current and previous month.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any


def _day_labels(year: int, month: int, count: int) -> list[str]:
    return [f"{year:04d}-{month:02d}-{day:02d}" for day in range(1, count + 1)]


def _month_labels(year: int, count: int) -> list[str]:
    return [f"{year:04d}-{month:02d}" for month in range(1, count + 1)]


def _day_window(range_key: str, year: int, month: int, count: int) -> dict[str, Any]:
    return {
        "range_key": range_key,
        "data": {"name": "", "from": f"{year:04d}/{month:02d}/01", "unit": "day", "max_num": count},
        "labels": _day_labels(year, month, count),
    }


def _month_window(range_key: str, year: int, count: int) -> dict[str, Any]:
    return {
        "range_key": range_key,
        "data": {"name": "", "from": f"{year:04d}/01/01", "unit": "month", "max_num": count},
        "labels": _month_labels(year, count),
    }


def build_user_info_statistics_requests(now: datetime | date | None = None) -> list[list[dict[str, Any]]]:
    """Build UserGetInfo statistics query windows, grouped per statistics grain.

    Each group is ordered oldest first and covers one contiguous series that is
    written to a single statistic id: previous + current month for day
    buckets, previous + current year for month buckets. Future buckets are
    never requested.
    """
    if now is None:
        now = datetime.today()
    today = now.date() if isinstance(now, datetime) else now

    if today.month == 1:
        prev_month_year, prev_month = today.year - 1, 12
    else:
        prev_month_year, prev_month = today.year, today.month - 1
    prev_month_days = calendar.monthrange(prev_month_year, prev_month)[1]

    return [
        [
            _day_window("previous_month", prev_month_year, prev_month, prev_month_days),
            _day_window("current_month", today.year, today.month, today.day),
        ],
        [
            _month_window("previous_year", today.year - 1, 12),
            _month_window("current_year", today.year, today.month),
        ],
    ]
