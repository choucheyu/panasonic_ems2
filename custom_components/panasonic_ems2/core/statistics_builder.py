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


def rebase_statistics(statistics: Sequence[Mapping[str, Any]], base_sum: float) -> list[dict[str, Any]]:
    """Shift every running ``sum`` by ``base_sum`` so a series continues an existing one."""
    return [{**row, "sum": row["sum"] + base_sum} for row in statistics]


def _grain_from_labels(labels: Sequence[str]) -> str:
    return "month" if labels and len(labels[0]) == 7 else "day"


def _device_name(gwid: str, devices_info: Mapping[str, Mapping[str, Any]]) -> str:
    safe_gwid = safe_statistic_object_id(gwid)
    return str(devices_info.get(gwid, {}).get("NickName") or safe_gwid)


def build_user_info_external_statistics_rows(
    *,
    segments: Sequence[tuple[Sequence[str], Sequence[Mapping[str, Any]]]],
    devices_info: Mapping[str, Mapping[str, Any]],
    domain: str,
    timezone: tzinfo,
) -> list[dict[str, Any]]:
    """Build recorder-agnostic external statistics rows for UserGetInfo metrics.

    ``segments`` are ``(labels, metrics)`` pairs for consecutive windows of one
    grain (oldest first). Each metric is joined across all segments into one
    series with a single running sum, so one statistic id has exactly one
    writer per refresh. Values are paired with labels per segment, so a short
    segment cannot shift the dates of the next one. A metric missing from any
    segment is skipped rather than written with a gap in its sum.
    """
    if not segments:
        return []

    grain = _grain_from_labels(segments[0][0])
    series: dict[tuple[str, str], dict[str, Any]] = {}
    for segment_index, (labels, metrics) in enumerate(segments):
        for metric in metrics:
            values = metric.get("values", [])
            if not values:
                continue
            key = (str(metric["gwid"]), str(metric["suffix"]))
            entry = series.setdefault(key, {"metric": metric, "labels": [], "values": [], "segments": set()})
            pairs = list(zip(labels, values))
            entry["labels"].extend(label for label, _ in pairs)
            entry["values"].extend(value for _, value in pairs)
            entry["segments"].add(segment_index)

    rows: list[dict[str, Any]] = []
    for (gwid, _suffix), entry in series.items():
        if len(entry["segments"]) != len(segments):
            continue
        metric = entry["metric"]
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
                "statistics": build_statistics_data(entry["labels"], entry["values"], timezone=timezone),
            }
        )

    return rows
