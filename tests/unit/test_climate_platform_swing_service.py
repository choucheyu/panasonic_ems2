"""Guards for Home Assistant climate swing service exposure."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIMATE_PLATFORM = ROOT / "custom_components" / "panasonic_ems2" / "climate.py"


def _panasonic_climate_class() -> ast.ClassDef:
    tree = ast.parse(CLIMATE_PLATFORM.read_text(encoding="utf-8"), filename=str(CLIMATE_PLATFORM))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PanasonicClimate":
            return node
    raise AssertionError("PanasonicClimate class not found")


def test_taiwan_climate_does_not_expose_home_assistant_swing_service() -> None:
    """Taiwan AC airflow direction is not HA's climate.set_swing_mode service."""
    source = CLIMATE_PLATFORM.read_text(encoding="utf-8")
    climate_class = _panasonic_climate_class()
    method_names = {
        node.name
        for node in climate_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    supported_features = next(
        node
        for node in climate_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "supported_features"
    )

    assert "async_set_swing_mode" not in method_names
    assert "ClimateEntityFeature.SWING_MODE" not in ast.unparse(supported_features)
    assert "CLIMATE_SWING_MODE" not in source
