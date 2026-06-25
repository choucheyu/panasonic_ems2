"""P0 guard for fail-closed unknown set_device command behavior."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"


def _method_node(class_name: str, method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    tree = ast.parse(CLOUD_PATH.read_text(encoding="utf-8"), filename=str(CLOUD_PATH))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"{class_name}.{method_name} not found")


@pytest.mark.p0_bug
def test_set_device_unknown_command_fails_closed_without_guessing_set_id() -> None:
    """Unknown write commands should not be synthesized from read command ids."""
    method = _method_node("PanasonicSmartHome", "set_device")
    source = ast.unparse(method)

    assert "int(func, 16) + 128" not in source
    assert "cmd is None" in source
    assert any(
        isinstance(node, (ast.Raise, ast.Return))
        for node in ast.walk(method)
        if hasattr(node, "lineno")
    )
