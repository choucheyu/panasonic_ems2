"""Status normalization helpers for PanasonicSmartHome cloud responses.

This module is intentionally Home Assistant independent. ``cloud.py`` keeps the
public ``PanasonicSmartHome`` method seam and delegates the pure status shaping
logic here.
"""

from __future__ import annotations

from typing import Any, Mapping

from .capabilities import commands_for_model
from .constants.climate import CLIMATE_PM25
from .constants.common import DEVICE_TYPE_WASHING_MACHINE
from .constants.dehumidifier import DEHUMIDIFIER_PM25
from .constants.fridge import FRIDGE_FREEZER_TEMPERATURE, FRIDGE_THAW_TEMPERATURE
from .constants.washing_machine import WASHING_MACHINE_TIMER_REMAINING_TIME

WASHER_MODELS_WITH_TIMER_SENTINEL = {
    "HDH",
    "KBS",
    "LMS",
    "LM",
    "DDH",
    "MDH",
    "DW",
    "LX128B",
}


def normalize_command_status(model_type: str, command_type: str, status: Any) -> tuple[str, Any]:
    """Apply known Panasonic cloud value normalizations."""
    try:
        new_status = int(status)
        if command_type in [CLIMATE_PM25, DEHUMIDIFIER_PM25] and int(status) == 65535:
            new_status = 0
        elif (
            model_type in WASHER_MODELS_WITH_TIMER_SENTINEL
            and command_type == WASHING_MACHINE_TIMER_REMAINING_TIME
        ):
            if int(status) > 65000:
                new_status = 0
        elif model_type in ["XGS"] and command_type in [
            FRIDGE_FREEZER_TEMPERATURE,
            FRIDGE_THAW_TEMPERATURE,
        ]:
            new_status = int(status) - 255
    except Exception:
        new_status = status
    return command_type, new_status


def merge_device_information_chunks(devices_info: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge multiple DeviceGetInfo chunk responses by DeviceID."""
    merged: dict[Any, dict[str, Any]] = {}
    order: list[Any] = []
    for device in devices_info:
        if not isinstance(device, dict):
            continue
        device_id = device.get("DeviceID")
        if device_id is None:
            continue
        if device_id not in merged:
            merged[device_id] = dict(device)
            merged[device_id]["Info"] = []
            order.append(device_id)
        info = device.get("Info", [])
        if isinstance(info, list):
            merged[device_id]["Info"].extend(info)
    return [merged[device_id] for device_id in order]


def refactor_device_information(model_type: str, devices_info: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert DeviceGetInfo ``Info`` arrays into status dictionaries."""
    devices_info = merge_device_information_chunks(devices_info)
    if len(devices_info) < 1:
        return []

    new_devices: list[dict[str, Any]] = []
    for device in devices_info:
        device_id = device.get("DeviceID", None)
        if device_id is None:
            continue
        device_info = device.get("Info", [])
        device_status: dict[str, Any] = {}
        for info in device_info:
            command_type, status = normalize_command_status(
                model_type,
                info["CommandType"],
                info["status"],
            )
            device_status[command_type] = status
        device["status"] = device_status
        device.pop("Info", None)
        new_devices.append(device)
    return new_devices


def build_offline_information(
    device_type: str | int,
    model_type: str,
    *,
    capability_registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build fallback offline info without zero-filling washing machines."""
    if str(device_type) == str(DEVICE_TYPE_WASHING_MACHINE):
        # Panasonic cloud 對洗衣機偶發回空 status 時不可用假資料 0 覆蓋狀態；
        # 否則 0x74 遙控、0x50 運轉情報等會被 HA 誤顯示為關閉/離線。
        return []

    commands = commands_for_model(
        capability_registry,
        device_type,
        model_type,
        apply_excess=False,
    )
    status = {key: 0 for key in commands}
    return [{"DeviceID": 1, "status": status}]
