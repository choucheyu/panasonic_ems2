"""Recorder side of the UserGetInfo external statistics import."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.core import HomeAssistant

from .statistics_builder import rebase_statistics

# Far enough back to find the previous month bucket of a year-grain series,
# plus gaps from downtime.
SUM_LOOKBACK_DAYS = 400


async def async_sum_before(hass: HomeAssistant, statistic_id: str, start: datetime) -> float:
    """Return the last recorded sum strictly before ``start`` (0 if none)."""
    stats = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start - timedelta(days=SUM_LOOKBACK_DAYS),
        start,
        {statistic_id},
        "hour",
        None,
        {"sum"},
    )
    previous = stats.get(statistic_id) or []
    if not previous:
        return 0.0
    return float(previous[-1].get("sum") or 0.0)


async def async_import_series(
    hass: HomeAssistant, metadata: Mapping[str, Any], statistics: Sequence[Mapping[str, Any]]
) -> None:
    """Import one re-fetched series so its running sum continues the stored one.

    Each refresh re-imports whole windows; starting their sum at the last row
    before the window keeps the statistic monotonic across refreshes, windows
    and month/year rollovers.
    """
    if not statistics:
        return
    base_sum = await async_sum_before(hass, metadata["statistic_id"], statistics[0]["start"])
    async_add_external_statistics(
        hass,
        metadata,
        [StatisticData(**row) for row in rebase_statistics(statistics, base_sum)],
    )
