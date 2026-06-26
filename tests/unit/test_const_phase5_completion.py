"""Phase 5 completion guards for full appliance-family const decomposition."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST = CORE / "const.py"
CONSTANTS_DIR = CORE / "constants"
DESCRIPTIONS_DIR = CORE / "entity_descriptions"

FAMILIES = (
    "airpurifier",
    "dehumidifier",
    "dryer",
    "erv",
    "fan",
    "fridge",
    "light",
    "washing_machine",
    "weight_plate",
)

FAMILY_PREFIXES = (
    "AIRPURIFIER_",
    "DEHUMIDIFIER_",
    "DRYER_",
    "ERV_",
    "FAN_",
    "FRIDGE_",
    "LIGHT_",
    "WASHING_MACHINE_",
    "WEIGHT_PLATE_",
)

DESCRIPTION_TUPLES = (
    "AIRPURIFIER_BINARY_SENSORS",
    "AIRPURIFIER_NUMBERS",
    "AIRPURIFIER_SELECTS",
    "AIRPURIFIER_SENSORS",
    "AIRPURIFIER_SWITCHES",
    "DEHUMIDIFIER_BINARY_SENSORS",
    "DEHUMIDIFIER_NUMBERS",
    "DEHUMIDIFIER_SELECTS",
    "DEHUMIDIFIER_SENSORS",
    "DEHUMIDIFIER_SWITCHES",
    "DRYER_BINARY_SENSORS",
    "DRYER_NUMBERS",
    "DRYER_SELECTS",
    "DRYER_SENSORS",
    "ERV_BINARY_SENSORS",
    "ERV_NUMBERS",
    "ERV_SELECTS",
    "ERV_SENSORS",
    "FRIDGE_BINARY_SENSORS",
    "FRIDGE_SELECTS",
    "FRIDGE_SENSORS",
    "FRIDGE_SWITCHES",
    "LIGHT_BINARY_SENSORS",
    "LIGHT_NUMBERS",
    "LIGHT_SENSORS",
    "LIGHT_SWITCHES",
    "WASHING_MACHINE_BINARY_SENSORS",
    "WASHING_MACHINE_HDH_SELECTS",
    "WASHING_MACHINE_SELECTS_BY_MODEL",
    "WASHING_MACHINE_SELECTS",
    "WASHING_MACHINE_SENSORS",
    "WASHING_MACHINE_SWITCHES",
    "WEIGHT_PLATE_SENSORS",
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


def test_remaining_appliance_constant_modules_exist_and_const_imports_them() -> None:
    source = CONST.read_text(encoding="utf-8")
    for family in FAMILIES:
        assert (CONSTANTS_DIR / f"{family}.py").exists()
        assert f"from .constants.{family} import" in source


def test_remaining_entity_description_modules_exist_and_const_imports_them() -> None:
    source = CONST.read_text(encoding="utf-8")
    for family in FAMILIES:
        if family == "fan":
            continue
        assert (DESCRIPTIONS_DIR / f"{family}.py").exists()
        assert f"from .entity_descriptions.{family} import" in source


def test_appliance_family_constants_are_not_directly_redefined_in_const() -> None:
    names = _assignment_names(CONST)
    still_direct = sorted(
        name
        for name in names
        if name.startswith(FAMILY_PREFIXES)
        and name not in {
            "WASHING_MACHINE_SELECTS_BY_MODEL",
            "WASHING_MACHINE_SELECTS",
        }
        and not name.endswith(("_BINARY_SENSORS", "_NUMBERS", "_SELECTS", "_SENSORS", "_SWITCHES"))
    )
    assert still_direct == []


def test_appliance_entity_description_tuples_are_not_directly_redefined_in_const() -> None:
    names = _assignment_names(CONST)
    assert sorted(name for name in DESCRIPTION_TUPLES if name in names) == []


def test_legacy_const_exports_key_appliance_constants_and_descriptions() -> None:
    env = load_constant_assignments(CONST)
    for symbol in (
        "AIRPURIFIER_POWER",
        "DEHUMIDIFIER_POWER",
        "DRYER_POWER",
        "ERV_POWER",
        "FAN_POWER",
        "FRIDGE_FREEZER_MODE",
        "LIGHT_POWER",
        "WASHING_MACHINE_REMOTE_CONTROL",
        "WEIGHT_PLATE_GET_WEIGHT",
        "ENTITY_UPDATE",
        "ENTITY_EMPTY",
        "ENTITY_WATER_USED",
        "ENTITY_WASH_TIMES",
    ):
        assert symbol in env

    source = CONST.read_text(encoding="utf-8")
    for tuple_name in DESCRIPTION_TUPLES:
        assert tuple_name in source
