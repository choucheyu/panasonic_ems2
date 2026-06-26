"""Pure builders for Home Assistant recorder statistics payloads.

This module intentionally avoids Home Assistant imports. It builds plain metadata
and statistic dictionaries that the integration layer can convert to recorder
classes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, tzinfo
from typing import Any


def safe_statistic_object_id(value: Any) -> str:
    """Return a stable external-statistics object id fragment."""
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")


def statistics_start_from_label(label: str, timezone: tzinfo) -> datetime:
    """Return timezone-aware local period start from a day/month UserGetInfo label."""
    if len(label) == 7:
        naive = datetime.strptime(label, "%Y-%m")
    else:
        naive = datetime.strptime(label, "%Y-%m-%d")

    if hasattr(timezone, "localize"):
        return timezone.localize(naive)  # type: ignore[attr-defined]
    return naive.replace(tzinfo=timezone)


def build_statistics_data(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    timezone: tzinfo,
) -> list[dict[str, Any]]:
    """Build recorder statistic data rows with a running sum."""
    statistics: list[dict[str, Any]] = []
    running_sum = 0.0
    for label, value in zip(labels, values):
        running_sum += value
        statistics.append(
            {
                "start": statistics_start_from_label(label, timezone),
                "state": value,
                "sum": running_sum,
            }
        )
    return statistics


def _grain_from_labels(labels: Sequence[str]) -> str:
    return "month" if labels and len(labels[0]) == 7 else "day"


def _device_name(gwid: str, devices_info: Mapping[str, Mapping[str, Any]]) -> str:
    safe_gwid = safe_statistic_object_id(gwid)
    return str(devices_info.get(gwid, {}).get("NickName") or safe_gwid)


def build_user_info_external_statistics_rows(
    *,
    metrics: Sequence[Mapping[str, Any]],
    labels: Sequence[str],
    range_key: str,
    devices_info: Mapping[str, Mapping[str, Any]],
    domain: str,
    timezone: tzinfo,
) -> list[dict[str, Any]]:
    """Build recorder-agnostic external statistics rows for UserGetInfo metrics."""
    grain = _grain_from_labels(labels)
    rows: list[dict[str, Any]] = []

    for metric in metrics:
        values = metric.get("values", [])
        if not values:
            continue

        gwid = str(metric["gwid"])
        safe_gwid = safe_statistic_object_id(gwid)
        metric_suffix = f"{metric['suffix']}_{grain}"
        rows.append(
            {
                "metadata": {
                    "mean_type": "none",
                    "has_sum": True,
                    "name": f"{_device_name(gwid, devices_info)} {metric['name']}",
                    "source": domain,
                    "statistic_id": f"{domain}:{safe_gwid}_{metric_suffix}",
                    "unit_class": metric["unit_class"],
                    "unit_of_measurement": metric["unit"],
                },
                "statistics": build_statistics_data(labels, values, timezone=timezone),
                "range_key": range_key,
            }
        )

    return rows
