"""Pure parsing helpers for Panasonic UserGetInfo time series.

The functions in this module intentionally avoid Home Assistant imports so raw
Panasonic cloud responses can be tested and normalized with plain Python.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def as_number(value: Any) -> float | None:
    """Return ``value`` as ``float`` when Panasonic returned a numeric bucket."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_number_list(values: Any) -> list[float]:
    """Return numeric Panasonic series values, dropping malformed buckets."""
    if not isinstance(values, list):
        return []

    parsed: list[float] = []
    for value in values:
        number = as_number(value)
        if number is not None:
            parsed.append(number)
    return parsed


def _gwid_from_info(gwinfo: Mapping[str, Any]) -> str | None:
    return gwinfo.get("GwID") or gwinfo.get("GWID")


def parse_user_info_series(
    info_type: str,
    response: Mapping[str, Any],
    devices_info: Mapping[str, Mapping[str, Any]],
    *,
    washing_machine_device_type: str,
) -> list[dict[str, Any]]:
    """Extract normalized series metric rows from a Panasonic ``UserGetInfo`` response.

    The returned rows are recorder-agnostic. Home Assistant-specific metadata and
    ``StatisticData`` conversion happen in the integration layer.
    """
    gw_list = response.get("GwList", [])
    if not isinstance(gw_list, list):
        return []

    rows: list[dict[str, Any]] = []
    for gwinfo in gw_list:
        if not isinstance(gwinfo, Mapping):
            continue

        gwid = _gwid_from_info(gwinfo)
        if not gwid or gwid not in devices_info:
            continue

        device_type = str(devices_info[gwid].get("DeviceType"))
        if info_type == "Power":
            values = as_number_list(gwinfo.get("kwh", []))
            if values:
                rows.append(
                    {
                        "gwid": gwid,
                        "suffix": "energy",
                        "name": "用電量",
                        "unit": "kWh",
                        "unit_class": "energy",
                        "values": values,
                    }
                )
            continue

        if info_type == "Other" and device_type == str(washing_machine_device_type):
            water_values = as_number_list(gwinfo.get("WM_WaterUsed", []))
            if water_values:
                rows.append(
                    {
                        "gwid": gwid,
                        "suffix": "water",
                        "name": "用水量",
                        "unit": "L",
                        "unit_class": "volume",
                        "values": water_values,
                    }
                )

            wash_count_values = as_number_list(gwinfo.get("WM_WashTime", []))
            if wash_count_values:
                rows.append(
                    {
                        "gwid": gwid,
                        "suffix": "wash_count",
                        "name": "洗衣次數",
                        "unit": "次",
                        "unit_class": None,
                        "values": wash_count_values,
                    }
                )

    return rows
