"""P0 guard for Panasonic dehumidifier device class."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HUMIDIFIER_PATH = ROOT / "custom_components" / "panasonic_ems2" / "humidifier.py"


def _class_node(class_name: str) -> ast.ClassDef:
    tree = ast.parse(HUMIDIFIER_PATH.read_text(encoding="utf-8"), filename=str(HUMIDIFIER_PATH))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"{class_name} not found")


@pytest.mark.p0_bug
@pytest.mark.xfail(
    strict=True,
    reason="known P0 bug: dehumidifier platform currently declares HumidifierDeviceClass.HUMIDIFIER",
)
def test_dehumidifier_entity_uses_dehumidifier_device_class() -> None:
    """A Panasonic dehumidifier entity should identify as a dehumidifier in HA."""
    klass = _class_node("PanasonicHumidifier")
    assigned_value = None
    for node in klass.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_attr_device_class":
                    assigned_value = ast.unparse(node.value)

    assert assigned_value == "HumidifierDeviceClass.DEHUMIDIFIER"
