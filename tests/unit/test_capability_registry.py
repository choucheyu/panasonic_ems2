"""Phase 4 guards for the model capability registry seam.

The registry must stay importable without Home Assistant so capability mapping can be
unit-tested separately from HA entity description objects in ``const.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from dataclasses import is_dataclass
from pathlib import Path
from types import ModuleType

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CONST = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
CAPABILITIES = ROOT / "custom_components" / "panasonic_ems2" / "core" / "capabilities.py"


def _load_capabilities_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("panasonic_capabilities_under_test", CAPABILITIES)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _const_assignment_names() -> set[str]:
    tree = ast.parse(CONST.read_text(encoding="utf-8"), filename=str(CONST))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_capability_module_defines_plain_python_model_capability_dataclass() -> None:
    module = _load_capabilities_module()

    assert hasattr(module, "ModelCapability")
    assert is_dataclass(module.ModelCapability)
    field_names = set(module.ModelCapability.__dataclass_fields__)
    assert {
        "base_commands",
        "extra_commands",
        "supplemental_commands",
        "excess_commands",
        "set_command_type",
        "range_family",
        "command_name_overrides",
        "command_range_overrides",
    } <= field_names


def test_build_capability_registry_preserves_existing_climate_and_hdh_mappings() -> None:
    module = _load_capabilities_module()
    env = load_constant_assignments(CONST)
    climate = str(env["DEVICE_TYPE_CLIMATE"])
    washer = str(env["DEVICE_TYPE_WASHING_MACHINE"])

    registry = module.build_capability_registry(
        commands_type=env["COMMANDS_TYPE"],
        extra_commands=env["EXTRA_COMMANDS"],
        supplemental_commands=env["SUPPLEMENTAL_COMMANDS"],
        excess_commands=env["EXCESS_COMMANDS"],
        set_command_type=env["SET_COMMAND_TYPE"],
        range_family={climate: env["CLIMATE_RANGE_FAMILY"]},
        command_name_overrides=env["COMMAND_NAME_OVERRIDES"],
        command_range_overrides=env["COMMAND_RANGE_OVERRIDES"],
    )

    climate_capability = registry[climate]
    washer_capability = registry[washer]

    assert climate_capability.base_commands == tuple(env["COMMANDS_TYPE"][climate])
    assert climate_capability.extra_commands["VX"] == tuple(env["CLIMATE_VX_COMMMANDS"])
    assert climate_capability.supplemental_commands["UX"] == tuple(env["CLIMATE_UX_SUPPLEMENTAL_COMMANDS"])
    assert climate_capability.range_family["UK"][env["CLIMATE_FAN_SPEED"]] == "PXGD"
    assert env["CLIMATE_OPERATING_MODE"] not in climate_capability.range_family["UK"]
    assert climate_capability.set_command_type[env["CLIMATE_VOICE"]] == 217

    assert washer_capability.extra_commands["HDH"] == tuple(env["WASHING_MACHINE_HDH_COMMANDS"])
    assert washer_capability.supplemental_commands["HDH"] == tuple(env["WASHING_MACHINE_HDH_SUPPLEMENTAL_COMMANDS"])
    assert washer_capability.excess_commands["HDH"] == tuple(env["WASHING_MACHINE_HDH_NON_COMMANDLIST_COMMANDS"])
    assert washer_capability.command_name_overrides[env["WASHING_MACHINE_REMOTE_CONTROL"]] == "遠端遙控"
    assert washer_capability.command_range_overrides[env["WASHING_MACHINE_REMOTE_CONTROL"]] == {
        "關閉": 0,
        "開啟": 1,
    }


def test_registry_round_trip_helpers_keep_legacy_constant_shapes() -> None:
    module = _load_capabilities_module()
    env = load_constant_assignments(CONST)
    climate = str(env["DEVICE_TYPE_CLIMATE"])

    registry = module.build_capability_registry(
        commands_type=env["COMMANDS_TYPE"],
        extra_commands=env["EXTRA_COMMANDS"],
        supplemental_commands=env["SUPPLEMENTAL_COMMANDS"],
        excess_commands=env["EXCESS_COMMANDS"],
        set_command_type=env["SET_COMMAND_TYPE"],
        range_family={climate: env["CLIMATE_RANGE_FAMILY"]},
        command_name_overrides=env["COMMAND_NAME_OVERRIDES"],
        command_range_overrides=env["COMMAND_RANGE_OVERRIDES"],
    )

    assert module.commands_type_from_registry(registry) == env["COMMANDS_TYPE"]
    assert module.extra_commands_from_registry(registry) == env["EXTRA_COMMANDS"]
    assert module.supplemental_commands_from_registry(registry) == env["SUPPLEMENTAL_COMMANDS"]
    assert module.excess_commands_from_registry(registry) == env["EXCESS_COMMANDS"]
    assert module.set_command_type_from_registry(registry) == env["SET_COMMAND_TYPE"]
    assert module.range_family_from_registry(registry, climate) == env["CLIMATE_RANGE_FAMILY"]


def test_const_exports_registry_without_removing_legacy_constants() -> None:
    source = CONST.read_text(encoding="utf-8")
    names = _const_assignment_names()

    assert "from .capabilities import" in source
    assert "build_capability_registry" in source
    assert "CAPABILITY_REGISTRY" in names

    # Existing public constants remain exported for current entity/platform code.
    for legacy_name in (
        "COMMANDS_TYPE",
        "EXTRA_COMMANDS",
        "SUPPLEMENTAL_COMMANDS",
        "EXCESS_COMMANDS",
        "SET_COMMAND_TYPE",
        "CLIMATE_RANGE_FAMILY",
        "COMMAND_NAME_OVERRIDES",
        "COMMAND_RANGE_OVERRIDES",
    ):
        assert legacy_name in names
