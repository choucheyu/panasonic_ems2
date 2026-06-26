"""Pure helpers for Panasonic command metadata normalization.

This module intentionally avoids importing Home Assistant so command metadata parsing
can be regression-tested with plain Python.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def _normalize_command_type(command_type: Any) -> str:
    """Normalize Panasonic command keys to the integration's canonical ``0xNN`` form."""
    return str(command_type).upper().replace("X", "x")


def _range_parameters(parameters_list: Iterable[list[Any]], parameter_type: str) -> dict[str, int]:
    """Build the Home Assistant option mapping for Panasonic range parameters."""
    maximum = 0
    minimum = 0

    for parameter in parameters_list:
        name = parameter[0]
        value = parameter[1]
        if name == "Min":
            minimum = value or 0
        if name == "Max":
            maximum = value or 1
        if name == "\u901a\u5e38":  # 通常
            minimum = value or 0
        if name == "\u6a21\u5f0f":  # 模式
            maximum = value or 1

    parsed: dict[str, int] = {}
    if maximum > 39:
        parsed[str(minimum)] = minimum
        parsed[str(maximum)] = maximum
    else:
        for value in range(minimum, maximum + 1):
            parsed[str(value)] = value

    if parameter_type == "rangeA":
        parsed["Auto"] = 0

    return parsed


def _enum_parameters(parameters_list: Iterable[list[Any]]) -> dict[str, Any]:
    """Build the Home Assistant option mapping for Panasonic enum parameters."""
    return {parameter[0]: parameter[1] for parameter in parameters_list}


def refactor_command_metadata(
    commands_list: Mapping[str, list[dict[str, Any]]],
    *,
    washing_machine_models: Iterable[str],
    washing_machine_2020_models: Iterable[str],
    washing_machine_operating_status: str,
    washing_machine_timer_remaining_time: str,
) -> dict[str, list[dict[str, Any]]]:
    """Normalize Panasonic ``CommandList`` metadata without mutating the input.

    The return shape mirrors the historical ``PanasonicSmartHome._commands_info``
    structure: each model type maps to device metadata entries with a string
    ``DeviceType``, ``CommandParameters`` option maps, and ``CommandName`` labels.
    """
    washer_model_types = set(washing_machine_models) | set(washing_machine_2020_models)
    normalized: dict[str, list[dict[str, Any]]] = {}

    for model_type, command_groups in commands_list.items():
        normalized_groups: list[dict[str, Any]] = []
        for command_group in command_groups:
            if "list" not in command_group:
                continue

            command_parameters: dict[str, dict[str, Any]] = {}
            command_names: dict[str, str] = {}

            for command in command_group["list"]:
                command_type = _normalize_command_type(command["CommandType"])
                parameter_type = command.get("ParameterType", "")
                parameters_list = command.get("Parameters", [])

                parameters: dict[str, Any] = {}
                if parameter_type == "enum":
                    parameters = _enum_parameters(parameters_list)
                    if (
                        model_type in washer_model_types
                        and command_type == washing_machine_operating_status
                    ):
                        parameters["Off"] = 0
                elif "range" in parameter_type:
                    parameters = _range_parameters(parameters_list, parameter_type)
                    if model_type in washer_model_types and command_type == "0x15":
                        command_parameters[washing_machine_timer_remaining_time] = parameters
                        command_names[washing_machine_timer_remaining_time] = command["CommandName"]

                command_parameters[command_type] = parameters
                command_names[command_type] = command["CommandName"]

            normalized_group = {
                key: value for key, value in command_group.items() if key != "list"
            }
            normalized_group["DeviceType"] = str(normalized_group["DeviceType"])
            normalized_group["CommandParameters"] = command_parameters
            normalized_group["CommandName"] = command_names
            normalized_groups.append(normalized_group)

        normalized[model_type] = normalized_groups

    return normalized
