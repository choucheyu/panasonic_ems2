"""Command-planning helpers for PanasonicSmartHome cloud polling.

This module keeps Home Assistant independent command list logic out of
``cloud.py`` while preserving the public ``PanasonicSmartHome`` method seam.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .capabilities import commands_for_model, supplemental_commands_for_model
from .constants.common import DEVICE_TYPE_FRIDGE, DEVICE_TYPE_LIGHT
from .constants.fridge import FRIDGE_XGS_COMMANDS
from .constants.light import (
    LIGHT_CHANNEL_1_TIMER_OFF,
    LIGHT_CHANNEL_1_TIMER_ON,
    LIGHT_CHANNEL_2_TIMER_OFF,
    LIGHT_CHANNEL_2_TIMER_ON,
    LIGHT_CHANNEL_3_TIMER_OFF,
    LIGHT_CHANNEL_3_TIMER_ON,
    LIGHT_OPERATION_STATE,
)

DEFAULT_POWER_COMMAND_TYPES = [{"CommandType": "0x00"}]


def _command_type_payload(commands: Sequence[str]) -> list[dict[str, str]]:
    return [{"CommandType": command} for command in commands]


def get_supplemental_keys(device: dict[str, Any], *, capability_registry: Mapping[str, Any]) -> list[str]:
    """Return isolated supplemental command keys for this device/model."""
    device_type = str(device.get("DeviceType", ""))
    model_type = device.get("ModelType", "")
    return list(
        supplemental_commands_for_model(
            capability_registry,
            device_type,
            model_type,
        )
    )


def build_polling_command_types(
    device_type: str | int,
    model_type: str,
    *,
    has_remote_commands: bool,
    capability_registry: Mapping[str, Any],
    model_jp_types: Sequence[str],
) -> list[dict[str, str]]:
    """Return DeviceGetInfo command payloads for one device/model."""
    if not has_remote_commands:
        return list(DEFAULT_POWER_COMMAND_TYPES)

    fallback_extra_commands = None
    fallback_excluded_model_types = None
    if int(device_type) == DEVICE_TYPE_FRIDGE:
        fallback_extra_commands = FRIDGE_XGS_COMMANDS
        fallback_excluded_model_types = list(model_jp_types)

    commands = commands_for_model(
        capability_registry,
        device_type,
        model_type,
        fallback_extra_commands=fallback_extra_commands,
        fallback_excluded_model_types=fallback_excluded_model_types,
    )
    if not commands:
        return list(DEFAULT_POWER_COMMAND_TYPES)
    return _command_type_payload(commands)


def build_light_device_command_types(
    device_type: str | int,
    model: str,
    device_id: int,
) -> list[dict[str, str]]:
    """Return per-device light channel command payloads."""
    commands: list[str] = []
    if int(device_type) == DEVICE_TYPE_LIGHT:
        if model in ["F540107", "F241107", "F540207", "F540207"] and device_id == 1:
            commands.extend([
                LIGHT_CHANNEL_1_TIMER_ON,
                LIGHT_CHANNEL_1_TIMER_OFF,
                LIGHT_OPERATION_STATE,
            ])
        elif model in ["F540207", "F540207"] and device_id == 2:
            commands.extend([LIGHT_CHANNEL_2_TIMER_ON, LIGHT_CHANNEL_2_TIMER_OFF])
        elif model == "F540307" and device_id == 3:
            commands.extend([LIGHT_CHANNEL_3_TIMER_ON, LIGHT_CHANNEL_3_TIMER_OFF])
    return _command_type_payload(commands)


def filter_supplemental_snapshot(
    snapshot: Any,
    keys: Sequence[str],
) -> dict[str, Any]:
    """Keep only requested command keys from a supplemental snapshot result."""
    if not isinstance(snapshot, dict):
        return {}
    requested = set(keys)
    return {key: value for key, value in snapshot.items() if key in requested}


def merge_supplemental_status(
    info_list: list[dict[str, Any]],
    supplemental_by_device_id: dict[Any, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge supplemental snapshots into existing Information status rows."""
    if not info_list or not supplemental_by_device_id:
        return info_list
    for device_info in info_list:
        device_id = device_info.get("DeviceID")
        extras = supplemental_by_device_id.get(device_id)
        if not extras:
            continue
        status = device_info.setdefault("status", {})
        for key, value in extras.items():
            status[key] = value
    return info_list
