"""P0 guard for PanasonicSwitch.is_on return contract."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SWITCH_PATH = ROOT / "custom_components" / "panasonic_ems2" / "switch.py"


def _method_node(class_name: str, method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    tree = ast.parse(SWITCH_PATH.read_text(encoding="utf-8"), filename=str(SWITCH_PATH))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"{class_name}.{method_name} not found")


@pytest.mark.p0_bug
@pytest.mark.xfail(
    strict=True,
    reason="known P0 bug: switch is_on returns STATE_UNAVAILABLE instead of bool | None",
)
def test_switch_is_on_returns_bool_or_none_not_state_unavailable_string() -> None:
    """Home Assistant SwitchEntity.is_on should return bool | None, not a state string."""
    method = _method_node("PanasonicSwitch", "is_on")
    returns_state_unavailable = any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Name)
        and node.value.id == "STATE_UNAVAILABLE"
        for node in ast.walk(method)
    )

    assert not returns_state_unavailable
    assert method.returns is None or ast.unparse(method.returns) in {"bool | None", "Optional[bool]"}
