"""UserGetInfo request-window helpers.

Kept Home Assistant independent so date/range behavior can be tested without HA.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def build_user_info_statistics_requests(now: datetime | None = None) -> list[dict[str, Any]]:
    """Build UserGetInfo statistics query ranges."""
    if now is None:
        now = datetime.today()
    today = now.date() if isinstance(now, datetime) else now

    def first_day_months_ago(months_ago: int):
        month_index = today.year * 12 + today.month - 1 - months_ago
        year = month_index // 12
        month = month_index % 12 + 1
        return today.replace(year=year, month=month, day=1)

    def day_labels(start, count: int):
        return [(start + timedelta(days=idx)).strftime("%Y-%m-%d") for idx in range(count)]

    def month_labels(start, count: int):
        labels = []
        for idx in range(count):
            month_index = start.year * 12 + start.month - 1 + idx
            year = month_index // 12
            month = month_index % 12 + 1
            labels.append(f"{year:04d}-{month:02d}")
        return labels

    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    last_30_start = today - timedelta(days=29)
    last_12_month_start = first_day_months_ago(11)
    current_month_days = (today - month_start).days + 1

    return [
        {
            "range_key": "today",
            "data": {"name": "", "from": today.strftime("%Y/%m/%d"), "unit": "day", "max_num": 1},
            "labels": day_labels(today, 1),
        },
        {
            "range_key": "current_month",
            "data": {"name": "", "from": month_start.strftime("%Y/%m/%d"), "unit": "day", "max_num": current_month_days},
            "labels": day_labels(month_start, current_month_days),
        },
        {
            "range_key": "current_year",
            "data": {"name": "", "from": year_start.strftime("%Y/%m/%d"), "unit": "month", "max_num": today.month},
            "labels": month_labels(year_start, today.month),
        },
        {
            "range_key": "last_30_days",
            "data": {"name": "", "from": last_30_start.strftime("%Y/%m/%d"), "unit": "day", "max_num": 30},
            "labels": day_labels(last_30_start, 30),
        },
        {
            "range_key": "last_12_months",
            "data": {"name": "", "from": last_12_month_start.strftime("%Y/%m/%d"), "unit": "month", "max_num": 12},
            "labels": month_labels(last_12_month_start, 12),
        },
    ]
