"""Registry tests for climate supplemental entity descriptions.

These tests protect the descriptor side of VX/UX supplemental support. They parse
``core/const.py`` with AST so the Phase 0 suite can run without importing Home
Assistant in the plain local Python environment.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import eval_literalish, load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST_PATH = CORE_PATH / "const.py"
CLIMATE_DESCRIPTIONS_PATH = CORE_PATH / "entity_descriptions" / "climate.py"

CLIMATE_DESCRIPTION_TUPLES = (
    "CLIMATE_BINARY_SENSORS",
    "CLIMATE_NUMBERS",
    "CLIMATE_SELECTS",
    "CLIMATE_SENSORS",
    "CLIMATE_SWITCHES",
)


def _load_tuple_call_attributes(tuple_name: str) -> dict[str, dict[str, Any]]:
    """Return descriptor keyword attributes keyed by resolved command key."""
    env = load_constant_assignments(CONST_PATH)
    source = CLIMATE_DESCRIPTIONS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CLIMATE_DESCRIPTIONS_PATH))

    for node in tree.body:
        assigned_names: list[str] = []
        value_node: ast.AST | None = None

        if isinstance(node, ast.Assign):
            assigned_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assigned_names = [node.target.id]
            value_node = node.value

        if tuple_name not in assigned_names:
            continue
        if not isinstance(value_node, ast.Tuple):
            raise AssertionError(f"{tuple_name} should be a tuple of entity descriptions")

        descriptions: dict[str, dict[str, Any]] = {}
        for element in value_node.elts:
            if not isinstance(element, ast.Call):
                continue

            attrs: dict[str, Any] = {}
            for keyword in element.keywords:
                if keyword.arg is None:
                    continue
                try:
                    attrs[keyword.arg] = eval_literalish(keyword.value, env)
                except (KeyError, TypeError):
                    # Device classes and Home Assistant enum objects are not needed here.
                    continue

            if "key" in attrs:
                descriptions[attrs["key"]] = attrs

        return descriptions

    raise AssertionError(f"{tuple_name} not found in {CLIMATE_DESCRIPTIONS_PATH}")


def _climate_descriptions_by_platform() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        tuple_name: _load_tuple_call_attributes(tuple_name)
        for tuple_name in CLIMATE_DESCRIPTION_TUPLES
    }


def _enabled_climate_supplemental_commands() -> set[str]:
    env = load_constant_assignments(CONST_PATH)
    climate_key = str(env["DEVICE_TYPE_CLIMATE"])
    supplemental = env["SUPPLEMENTAL_COMMANDS"][climate_key]

    enabled: set[str] = set()
    for command_list in supplemental.values():
        enabled.update(command_list)
    return enabled


def test_verified_supplemental_commands_have_expected_entity_platforms() -> None:
    env = load_constant_assignments(CONST_PATH)
    descriptions = _climate_descriptions_by_platform()

    assert env["CLIMATE_PM25"] in descriptions["CLIMATE_SENSORS"]
    assert env["CLIMATE_HUMIDITY_INDOOR"] in descriptions["CLIMATE_SENSORS"]
    assert env["CLIMATE_MONITOR_MILDEW"] in descriptions["CLIMATE_SWITCHES"]
    assert env["CLIMATE_IMMEDIATE_MILDEW_DRY"] in descriptions["CLIMATE_SELECTS"]
    assert env["CLIMATE_VOICE"] in descriptions["CLIMATE_SWITCHES"]


def test_enabled_climate_supplemental_commands_have_entity_descriptions() -> None:
    descriptions = _climate_descriptions_by_platform()
    described_keys = set().union(*(platform.keys() for platform in descriptions.values()))
    enabled_supplemental = _enabled_climate_supplemental_commands()

    assert enabled_supplemental <= described_keys


def test_supplemental_entity_labels_are_taiwan_friendly() -> None:
    env = load_constant_assignments(CONST_PATH)
    descriptions = _climate_descriptions_by_platform()

    sensors = descriptions["CLIMATE_SENSORS"]
    switches = descriptions["CLIMATE_SWITCHES"]
    selects = descriptions["CLIMATE_SELECTS"]

    assert sensors[env["CLIMATE_PM25"]]["name"] == "PM2.5"
    assert sensors[env["CLIMATE_HUMIDITY_INDOOR"]]["name"] == "室內濕度"
    assert switches[env["CLIMATE_MONITOR_MILDEW"]]["name"] == "防霉監控"
    assert switches[env["CLIMATE_VOICE"]]["name"] == "聲控開關"
    assert selects[env["CLIMATE_IMMEDIATE_MILDEW_DRY"]]["name"] == "立即乾燥防霉"


def test_immediate_mildew_dry_select_keeps_known_vx_ux_options() -> None:
    env = load_constant_assignments(CONST_PATH)
    selects = _climate_descriptions_by_platform()["CLIMATE_SELECTS"]
    descriptor = selects[env["CLIMATE_IMMEDIATE_MILDEW_DRY"]]

    assert descriptor["options"] == ["關閉", "10分鐘行程", "20分鐘行程", "40分鐘行程", "60分鐘行程"]
    assert descriptor["options_value"] == ["0", "1", "2", "3", "4"]


def test_no_enabled_supplemental_command_is_described_only_as_binary_or_number() -> None:
    descriptions = _climate_descriptions_by_platform()
    enabled_supplemental = _enabled_climate_supplemental_commands()
    active_entity_keys = (
        set(descriptions["CLIMATE_SENSORS"])
        | set(descriptions["CLIMATE_SELECTS"])
        | set(descriptions["CLIMATE_SWITCHES"])
    )

    assert enabled_supplemental <= active_entity_keys
