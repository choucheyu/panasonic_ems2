"""Declarative Panasonic EMS2 model capability registry.

This module is intentionally Home Assistant independent so command/capability
relationships can be tested without importing HA entity description classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


CommandList = tuple[str, ...]
ModelCommandMap = dict[str, CommandList]
NestedMapping = dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ModelCapability:
    """Capability bundle for one Panasonic device type."""

    base_commands: CommandList = ()
    extra_commands: ModelCommandMap = field(default_factory=dict)
    supplemental_commands: ModelCommandMap = field(default_factory=dict)
    excess_commands: ModelCommandMap = field(default_factory=dict)
    set_command_type: dict[str, int] = field(default_factory=dict)
    range_family: NestedMapping = field(default_factory=dict)
    command_name_overrides: dict[str, str] = field(default_factory=dict)
    command_range_overrides: NestedMapping = field(default_factory=dict)

    # Preserve whether legacy maps intentionally exported an empty dict for a
    # device type. This lets round-trip helpers keep the old public constant
    # shape while code can still use the normalized fields above.
    extra_commands_defined: bool = False
    supplemental_commands_defined: bool = False
    excess_commands_defined: bool = False
    set_command_type_defined: bool = False


def _ordered_device_types(*maps: Mapping[str, Any]) -> list[str]:
    """Return map keys in first-seen order across legacy capability maps."""
    device_types: list[str] = []
    seen: set[str] = set()
    for mapping in maps:
        for device_type in mapping:
            if device_type in seen:
                continue
            seen.add(device_type)
            device_types.append(device_type)
    return device_types


def _commands(values: list[str] | tuple[str, ...] | None) -> CommandList:
    return tuple(values or ())


def _model_commands(mapping: Mapping[str, list[str] | tuple[str, ...]] | None) -> ModelCommandMap:
    if not mapping:
        return {}
    return {str(model_type): _commands(commands) for model_type, commands in mapping.items()}


def _flat_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    if not mapping:
        return {}
    return {str(key): value for key, value in mapping.items()}


def _nested_mapping(mapping: Mapping[str, Mapping[str, Any]] | None) -> NestedMapping:
    if not mapping:
        return {}
    return {
        str(outer_key): {str(inner_key): value for inner_key, value in inner_value.items()}
        for outer_key, inner_value in mapping.items()
    }


def build_capability_registry(
    *,
    commands_type: Mapping[str, list[str] | tuple[str, ...]],
    extra_commands: Mapping[str, Mapping[str, list[str] | tuple[str, ...]]] | None = None,
    supplemental_commands: Mapping[str, Mapping[str, list[str] | tuple[str, ...]]] | None = None,
    excess_commands: Mapping[str, Mapping[str, list[str] | tuple[str, ...]]] | None = None,
    set_command_type: Mapping[str, Mapping[str, int]] | None = None,
    range_family: Mapping[str, Mapping[str, Mapping[str, str]]] | None = None,
    command_name_overrides: Mapping[str, Mapping[str, str]] | None = None,
    command_range_overrides: Mapping[str, Mapping[str, Mapping[str, int]]] | None = None,
) -> dict[str, ModelCapability]:
    """Build a normalized registry from the legacy capability constants."""
    extra_commands = extra_commands or {}
    supplemental_commands = supplemental_commands or {}
    excess_commands = excess_commands or {}
    set_command_type = set_command_type or {}
    range_family = range_family or {}
    command_name_overrides = command_name_overrides or {}
    command_range_overrides = command_range_overrides or {}

    registry: dict[str, ModelCapability] = {}
    for device_type in _ordered_device_types(
        commands_type,
        extra_commands,
        supplemental_commands,
        excess_commands,
        set_command_type,
        range_family,
        command_name_overrides,
        command_range_overrides,
    ):
        registry[device_type] = ModelCapability(
            base_commands=_commands(commands_type.get(device_type)),
            extra_commands=_model_commands(extra_commands.get(device_type)),
            supplemental_commands=_model_commands(supplemental_commands.get(device_type)),
            excess_commands=_model_commands(excess_commands.get(device_type)),
            set_command_type={str(key): int(value) for key, value in set_command_type.get(device_type, {}).items()},
            range_family=_nested_mapping(range_family.get(device_type)),
            command_name_overrides={
                str(key): str(value)
                for key, value in command_name_overrides.get(device_type, {}).items()
            },
            command_range_overrides=_nested_mapping(command_range_overrides.get(device_type)),
            extra_commands_defined=device_type in extra_commands,
            supplemental_commands_defined=device_type in supplemental_commands,
            excess_commands_defined=device_type in excess_commands,
            set_command_type_defined=device_type in set_command_type,
        )
    return registry


def commands_type_from_registry(registry: Mapping[str, ModelCapability]) -> dict[str, list[str]]:
    """Rebuild the legacy ``COMMANDS_TYPE`` shape from a capability registry."""
    return {device_type: list(capability.base_commands) for device_type, capability in registry.items()}


def extra_commands_from_registry(registry: Mapping[str, ModelCapability]) -> dict[str, dict[str, list[str]]]:
    """Rebuild the legacy ``EXTRA_COMMANDS`` shape."""
    return {
        device_type: {model_type: list(commands) for model_type, commands in capability.extra_commands.items()}
        for device_type, capability in registry.items()
        if capability.extra_commands_defined
    }


def supplemental_commands_from_registry(registry: Mapping[str, ModelCapability]) -> dict[str, dict[str, list[str]]]:
    """Rebuild the legacy ``SUPPLEMENTAL_COMMANDS`` shape."""
    return {
        device_type: {model_type: list(commands) for model_type, commands in capability.supplemental_commands.items()}
        for device_type, capability in registry.items()
        if capability.supplemental_commands_defined
    }


def excess_commands_from_registry(registry: Mapping[str, ModelCapability]) -> dict[str, dict[str, list[str]]]:
    """Rebuild the legacy ``EXCESS_COMMANDS`` shape."""
    return {
        device_type: {model_type: list(commands) for model_type, commands in capability.excess_commands.items()}
        for device_type, capability in registry.items()
        if capability.excess_commands_defined
    }


def set_command_type_from_registry(registry: Mapping[str, ModelCapability]) -> dict[str, dict[str, int]]:
    """Rebuild the legacy ``SET_COMMAND_TYPE`` shape."""
    return {
        device_type: dict(capability.set_command_type)
        for device_type, capability in registry.items()
        if capability.set_command_type_defined
    }


def range_family_from_registry(
    registry: Mapping[str, ModelCapability],
    device_type: str,
) -> dict[str, dict[str, str]]:
    """Return the model-family range aliases for one device type."""
    capability = registry.get(device_type)
    if capability is None:
        return {}
    return {model_type: dict(commands) for model_type, commands in capability.range_family.items()}
