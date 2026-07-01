"""Guards for climate mode fallbacks when Panasonic omits command ranges."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tests.helpers.source_parsing import load_constant_assignments, load_method_function

ROOT = Path(__file__).resolve().parents[2]
CLIMATE_PLATFORM = ROOT / "custom_components" / "panasonic_ems2" / "climate.py"
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"


class HVACMode:
    """Small Home Assistant HVACMode stand-in for source-extracted tests."""

    OFF = "off"
    COOL = "cool"
    DRY = "dry"
    FAN_ONLY = "fan_only"
    AUTO = "auto"
    HEAT = "heat"


class _EmptyRangeClient:
    def get_range(self, _gwid: str, _command: str) -> dict[str, Any]:
        return {}


def _load_top_level_function(
    function_name: str,
    globals_env: dict[str, Any],
):
    source = CLIMATE_PLATFORM.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CLIMATE_PLATFORM))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            segment = ast.get_source_segment(source, node)
            if segment is None:
                raise AssertionError(f"source segment not found for {function_name}")
            namespace = dict(globals_env)
            exec(textwrap.dedent(segment), namespace)
            return namespace[function_name]
    raise AssertionError(f"{function_name} not found")


def _climate_globals() -> dict[str, Any]:
    env = load_constant_assignments(CONST_PATH)
    globals_env = {
        "HVACMode": HVACMode,
        "DEVICE_TYPE_CLIMATE": env["DEVICE_TYPE_CLIMATE"],
        "DEVICE_TYPE_ERV": env["DEVICE_TYPE_ERV"],
        "CLIMATE_OPERATING_MODE": env["CLIMATE_OPERATING_MODE"],
        "CLIMATE_POWER": env["CLIMATE_POWER"],
        "CLIMATE_FAN_SPEED": env["CLIMATE_FAN_SPEED"],
        "CLIMATE_RANGE_FAMILY": env["CLIMATE_RANGE_FAMILY"],
        "CLIMATE_AVAILABLE_MODES": {
            HVACMode.COOL: 0,
            HVACMode.DRY: 1,
            HVACMode.FAN_ONLY: 2,
            HVACMode.AUTO: 3,
            HVACMode.HEAT: 4,
        },
        "CLIMATE_AVAILABLE_PRESET_MODES": {
            "0x1A": "Boost",
            "0x1B": "Eco",
            "0x05": "Sleep",
        },
        "CLIMATE_AVAILABLE_FAN_MODES": {
            "Auto": 0,
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
        },
        "PRESET_NONE": "none",
        "ERV_POWER": "0xERV_POWER",
        "ERV_OPERATING_MODE": "0xERV_MODE",
        "ERV_FAN_SPEED": "0xERV_FAN_SPEED",
        "ERV_AVAILABLE_MODES": {"erv_auto": 0},
        "ERV_AVAILABLE_FAN_MODES": {"erv_auto": 0},
    }
    globals_env["_fallback_climate_hvac_modes"] = _load_top_level_function(
        "_fallback_climate_hvac_modes",
        globals_env,
    )
    globals_env["_fallback_climate_fan_modes"] = _load_top_level_function(
        "_fallback_climate_fan_modes",
        globals_env,
    )
    globals_env["get_key_from_dict"] = _load_top_level_function(
        "get_key_from_dict",
        globals_env,
    )
    return globals_env


def _climate_entity(model_type: str) -> SimpleNamespace:
    env = load_constant_assignments(CONST_PATH)
    return SimpleNamespace(
        _device_type=env["DEVICE_TYPE_CLIMATE"],
        client=_EmptyRangeClient(),
        device_gwid="GWID_CLIMATE",
        info={"ModelType": model_type},
    )


def _climate_entity_without_status() -> SimpleNamespace:
    env = load_constant_assignments(CONST_PATH)
    return SimpleNamespace(
        _device_type=env["DEVICE_TYPE_CLIMATE"],
        coordinator=SimpleNamespace(data={}),
        get_status=lambda _data: {},
    )


def test_unknown_climate_with_missing_range_falls_back_without_heat() -> None:
    hvac_modes = load_method_function(
        CLIMATE_PLATFORM,
        class_name="PanasonicClimate",
        method_name="hvac_modes",
        globals_env=_climate_globals(),
    )

    assert hvac_modes(_climate_entity("UNKNOWN")) == [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
    ]


def test_known_heat_capable_family_with_missing_range_includes_heat() -> None:
    hvac_modes = load_method_function(
        CLIMATE_PLATFORM,
        class_name="PanasonicClimate",
        method_name="hvac_modes",
        globals_env=_climate_globals(),
    )

    assert hvac_modes(_climate_entity("VX")) == [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
        HVACMode.HEAT,
    ]


def test_climate_with_missing_fan_range_falls_back_to_auto_and_levels_one_to_five() -> None:
    fan_modes = load_method_function(
        CLIMATE_PLATFORM,
        class_name="PanasonicClimate",
        method_name="fan_modes",
        globals_env=_climate_globals(),
    )

    assert fan_modes(_climate_entity("UNKNOWN")) == ["Auto", "1", "2", "3", "4", "5"]


def test_climate_fan_mode_returns_none_when_status_is_absent() -> None:
    fan_mode = load_method_function(
        CLIMATE_PLATFORM,
        class_name="PanasonicClimate",
        method_name="fan_mode",
        globals_env=_climate_globals(),
    )

    assert fan_mode(_climate_entity_without_status()) is None


def test_climate_preset_mode_returns_none_option_when_status_is_absent() -> None:
    preset_mode = load_method_function(
        CLIMATE_PLATFORM,
        class_name="PanasonicClimate",
        method_name="preset_mode",
        globals_env=_climate_globals(),
    )

    assert preset_mode(_climate_entity_without_status()) == "none"
