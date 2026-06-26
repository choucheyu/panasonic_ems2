"""Phase 5 continuation guards for climate entity-description decomposition.

This slice is intentionally about module boundaries and legacy export stability:
``core.const`` should keep exporting the climate tuples, but the tuple definitions
move to a HA-dependent climate entity-description module.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import eval_literalish, load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST = CORE / "const.py"
CLIMATE_DESCRIPTIONS = CORE / "entity_descriptions" / "climate.py"
BASE_DESCRIPTIONS = CORE / "entity_descriptions" / "base.py"

CLIMATE_DESCRIPTION_TUPLES = (
    "CLIMATE_BINARY_SENSORS",
    "CLIMATE_NUMBERS",
    "CLIMATE_SELECTS",
    "CLIMATE_SENSORS",
    "CLIMATE_SWITCHES",
)


def _assignment_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _tuple_call_attributes(path: Path, tuple_name: str) -> dict[str, dict[str, Any]]:
    env = load_constant_assignments(CONST)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in tree.body:
        value: ast.AST | None = None
        names: list[str] = []
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
            value = node.value

        if tuple_name not in names:
            continue
        if not isinstance(value, ast.Tuple):
            raise AssertionError(f"{tuple_name} should be a tuple")

        descriptions: dict[str, dict[str, Any]] = {}
        for element in value.elts:
            if not isinstance(element, ast.Call):
                continue
            attrs: dict[str, Any] = {}
            for keyword in element.keywords:
                if keyword.arg is None:
                    continue
                try:
                    attrs[keyword.arg] = eval_literalish(keyword.value, env)
                except (KeyError, TypeError):
                    # HA enum objects are import/runtime concerns, not needed here.
                    continue
            if "key" in attrs:
                descriptions[attrs["key"]] = attrs
        return descriptions

    raise AssertionError(f"{tuple_name} not found in {path}")


def test_climate_entity_description_module_exists_with_all_climate_tuples() -> None:
    assert BASE_DESCRIPTIONS.exists()
    assert CLIMATE_DESCRIPTIONS.exists()

    source = CLIMATE_DESCRIPTIONS.read_text(encoding="utf-8")
    names = _assignment_names(CLIMATE_DESCRIPTIONS)

    assert "from .base import" in source
    for tuple_name in CLIMATE_DESCRIPTION_TUPLES:
        assert tuple_name in names


def test_const_imports_climate_entity_descriptions_without_redefining_them() -> None:
    source = CONST.read_text(encoding="utf-8")
    names = _assignment_names(CONST)

    assert "from .entity_descriptions.climate import" in source
    for tuple_name in CLIMATE_DESCRIPTION_TUPLES:
        assert tuple_name not in names


def test_climate_entity_description_content_is_preserved_in_new_module() -> None:
    env = load_constant_assignments(CONST)
    sensors = _tuple_call_attributes(CLIMATE_DESCRIPTIONS, "CLIMATE_SENSORS")
    selects = _tuple_call_attributes(CLIMATE_DESCRIPTIONS, "CLIMATE_SELECTS")
    switches = _tuple_call_attributes(CLIMATE_DESCRIPTIONS, "CLIMATE_SWITCHES")
    numbers = _tuple_call_attributes(CLIMATE_DESCRIPTIONS, "CLIMATE_NUMBERS")
    binary_sensors = _tuple_call_attributes(CLIMATE_DESCRIPTIONS, "CLIMATE_BINARY_SENSORS")

    assert sensors[env["CLIMATE_TEMPERATURE_INDOOR"]]["name"] == "室內溫度"
    assert sensors[env["CLIMATE_PM25"]]["name"] == "PM2.5"
    assert sensors[env["CLIMATE_HUMIDITY_INDOOR"]]["name"] == "室內濕度"

    assert selects[env["CLIMATE_IMMEDIATE_MILDEW_DRY"]]["name"] == "立即乾燥防霉"
    assert selects[env["CLIMATE_IMMEDIATE_MILDEW_DRY"]]["options"] == [
        "關閉",
        "10分鐘行程",
        "20分鐘行程",
        "40分鐘行程",
        "60分鐘行程",
    ]

    assert switches[env["CLIMATE_VOICE"]]["name"] == "聲控開關"
    assert switches[env["CLIMATE_BUZZER"]]["reverse_state"] is True
    assert numbers[env["CLIMATE_TIMER_ON"]]["native_max_value"] == 1440
    assert binary_sensors[env["ENTITY_UPDATE"]]["name"] == "版本更新"


def test_legacy_const_still_exports_climate_description_tuple_names() -> None:
    source = CONST.read_text(encoding="utf-8")
    for tuple_name in CLIMATE_DESCRIPTION_TUPLES:
        assert tuple_name in source
