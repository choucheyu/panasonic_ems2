"""Phase 6 guards for runtime migration from legacy maps to capability registry."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST = CORE / "const.py"
CLOUD = CORE / "cloud.py"
CAPABILITIES = CORE / "capabilities.py"

LEGACY_RUNTIME_MAPS = {
    "COMMANDS_TYPE",
    "EXTRA_COMMANDS",
    "SUPPLEMENTAL_COMMANDS",
    "EXCESS_COMMANDS",
    "SET_COMMAND_TYPE",
    "COMMAND_NAME_OVERRIDES",
    "COMMAND_RANGE_OVERRIDES",
    "CLIMATE_RANGE_FAMILY",
}


def _load_capabilities_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("panasonic_capabilities_phase6", CAPABILITIES)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _registry(module: ModuleType, env: dict[str, object]):
    climate = str(env["DEVICE_TYPE_CLIMATE"])
    return module.build_capability_registry(
        commands_type=env["COMMANDS_TYPE"],
        extra_commands=env["EXTRA_COMMANDS"],
        supplemental_commands=env["SUPPLEMENTAL_COMMANDS"],
        excess_commands=env["EXCESS_COMMANDS"],
        set_command_type=env["SET_COMMAND_TYPE"],
        range_family={climate: env["CLIMATE_RANGE_FAMILY"]},
        command_name_overrides=env["COMMAND_NAME_OVERRIDES"],
        command_range_overrides=env["COMMAND_RANGE_OVERRIDES"],
    )


def test_cloud_runtime_imports_registry_not_legacy_capability_maps() -> None:
    """Runtime cloud logic should consume CAPABILITY_REGISTRY, not raw legacy maps."""
    source = CLOUD.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CLOUD))

    imported_from_const: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module == "const":
            imported_from_const.update(alias.name for alias in node.names)

    assert "CAPABILITY_REGISTRY" in imported_from_const
    assert imported_from_const.isdisjoint(LEGACY_RUNTIME_MAPS)

    class_node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PanasonicSmartHome")
    runtime_method_names = {
        "_get_supplemental_keys",
        "_get_commands",
        "_offline_info",
        "set_device",
        "get_command_name",
        "get_range",
    }
    for method in class_node.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) or method.name not in runtime_method_names:
            continue
        names = {node.id for node in ast.walk(method) if isinstance(node, ast.Name)}
        assert names.isdisjoint(LEGACY_RUNTIME_MAPS), method.name


def test_registry_runtime_helpers_preserve_hdh_and_climate_lookup_behavior() -> None:
    module = _load_capabilities_module()
    env = load_constant_assignments(CONST)
    registry = _registry(module, env)

    washer = str(env["DEVICE_TYPE_WASHING_MACHINE"])
    climate = str(env["DEVICE_TYPE_CLIMATE"])

    assert list(module.commands_for_model(registry, washer, "HDH")) == [
        command
        for command in env["COMMANDS_TYPE"][washer] + env["EXTRA_COMMANDS"][washer]["HDH"]
        if command not in set(env["EXCESS_COMMANDS"][washer]["HDH"])
    ]
    assert list(module.supplemental_commands_for_model(registry, washer, "HDH")) == env["SUPPLEMENTAL_COMMANDS"][washer]["HDH"]
    assert module.set_command_id(registry, washer, env["WASHING_MACHINE_POSTPONE_DRYING_TIME"]) == env["SET_COMMAND_TYPE"][washer][env["WASHING_MACHINE_POSTPONE_DRYING_TIME"]]
    assert module.set_command_id(registry, washer, env["WASHING_MACHINE_POSTPONE_DRYING"]) is None
    assert module.command_name_override(registry, washer, env["WASHING_MACHINE_REMOTE_CONTROL"]) == "遠端遙控"
    assert module.command_range_override(registry, washer, env["WASHING_MACHINE_REMOTE_CONTROL"]) == {
        "關閉": 0,
        "開啟": 1,
    }

    assert list(module.range_lookup_models(registry, climate, "UK", env["CLIMATE_FAN_SPEED"])) == ["UK", "PXGD"]
    assert list(module.range_lookup_models(registry, climate, "UK", env["CLIMATE_OPERATING_MODE"])) == ["UK"]


def test_registry_runtime_helpers_preserve_fridge_xgs_fallback_policy() -> None:
    """Registry helper keeps the legacy XGS fallback when non-JP fridge lacks extra commands."""
    module = _load_capabilities_module()
    env = load_constant_assignments(CONST)
    registry = _registry(module, env)
    fridge = str(env["DEVICE_TYPE_FRIDGE"])

    base = env["COMMANDS_TYPE"][fridge]
    assert list(
        module.commands_for_model(
            registry,
            fridge,
            "UNKNOWN_TW_MODEL",
            fallback_extra_commands=env["FRIDGE_XGS_COMMANDS"],
        )
    ) == base + env["FRIDGE_XGS_COMMANDS"]
    assert list(
        module.commands_for_model(
            registry,
            fridge,
            "F655",
            fallback_extra_commands=env["FRIDGE_XGS_COMMANDS"],
            fallback_excluded_model_types=env["MODEL_JP_TYPES"],
        )
    ) == base + env["EXTRA_COMMANDS"][fridge]["F655"]
