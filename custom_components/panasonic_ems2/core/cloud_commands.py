"""Command-planning helpers for PanasonicSmartHome cloud polling.

This module keeps Home Assistant independent command list logic out of
``cloud.py`` while preserving the public ``PanasonicSmartHome`` method seam.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .capabilities import commands_for_model, supplemental_commands_for_model
from .constants.common import (
    DEVICE_TYPE_DRYER,
    DEVICE_TYPE_FRIDGE,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_WASHING_MACHINE,
)
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
DEVICE_GET_INFO_COMMAND_CHUNK_SIZE = 4
DEVICE_GET_INFO_REQUEST_TIMEOUT_SECONDS = 5


def chunk_command_type_payload(
    command_types: Sequence[Mapping[str, Any]],
    *,
    max_commands: int = DEVICE_GET_INFO_COMMAND_CHUNK_SIZE,
) -> list[list[dict[str, Any]]]:
    """Dedupe and split DeviceGetInfo CommandTypes into bounded chunks."""
    if max_commands < 1:
        raise ValueError("max_commands must be positive")

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in command_types:
        if not isinstance(item, Mapping):
            continue
        command_type = item.get("CommandType")
        if not isinstance(command_type, str) or command_type in seen:
            continue
        seen.add(command_type)
        deduped.append(dict(item))

    return [
        deduped[index : index + max_commands]
        for index in range(0, len(deduped), max_commands)
    ]


def _command_type_payload(commands: Sequence[str]) -> list[dict[str, str]]:
    return [{"CommandType": command} for command in commands]


def remote_command_types_for_model(
    command_metadata: Mapping[str, Sequence[Mapping[str, Any]]],
    device_type: str | int,
    model_type: str,
) -> list[str] | None:
    """Return cloud-declared CommandList keys for one model/device type.

    ``None`` means Panasonic did not provide metadata for this model/type.
    An empty list means metadata exists but declares no commands, which callers
    must not confuse with a broad local capability fallback.
    """
    groups = command_metadata.get(model_type)
    if groups is None:
        return None
    for group in groups:
        if str(group.get("DeviceType")) != str(device_type):
            continue
        declared = group.get("CommandTypes")
        if declared is not None:
            return [str(command) for command in declared]
        parameters = group.get("CommandParameters", {})
        return [str(command) for command in parameters]
    return None


def no_remote_command_types_for_model(
    no_remote_command_types: Mapping[str, Mapping[str, Sequence[str]]],
    device_type: str | int,
    model_type: str,
) -> list[str] | None:
    """Return known-safe local command keys when Panasonic omits CommandList."""
    commands = no_remote_command_types.get(str(device_type), {}).get(model_type)
    if commands is None:
        return None
    return [str(command) for command in commands]


DECLARED_COMMAND_POLLING_DEVICE_TYPES = (
    DEVICE_TYPE_WASHING_MACHINE,
    DEVICE_TYPE_DRYER,
)


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
    remote_command_types: Sequence[str] | None = None,
    no_remote_command_types: Sequence[str] | None = None,
    declared_command_device_types: Sequence[str | int] = DECLARED_COMMAND_POLLING_DEVICE_TYPES,
    capability_registry: Mapping[str, Any],
    model_jp_types: Sequence[str],
) -> list[dict[str, str]]:
    """Return DeviceGetInfo command payloads for one device/model."""
    if remote_command_types is not None and str(device_type) in {
        str(allowed_type) for allowed_type in declared_command_device_types
    }:
        if remote_command_types:
            return _command_type_payload(remote_command_types)
        if no_remote_command_types:
            return _command_type_payload(no_remote_command_types)
        return list(DEFAULT_POWER_COMMAND_TYPES)

    if no_remote_command_types and str(device_type) in {
        str(allowed_type) for allowed_type in declared_command_device_types
    }:
        return _command_type_payload(no_remote_command_types)

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
