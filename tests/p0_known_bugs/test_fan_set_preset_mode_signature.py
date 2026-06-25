"""P0 guard for PanasonicFan.async_set_preset_mode set_device signature."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FAN_PATH = ROOT / "custom_components" / "panasonic_ems2" / "fan.py"


def _method_node(class_name: str, method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    tree = ast.parse(FAN_PATH.read_text(encoding="utf-8"), filename=str(FAN_PATH))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"{class_name}.{method_name} not found")


def _is_self_client_set_device_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "set_device"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "client"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "self"
    )


@pytest.mark.p0_bug
@pytest.mark.xfail(
    strict=True,
    reason="known P0 bug: fan preset mode currently passes an extra argument to set_device",
)
def test_fan_set_preset_mode_calls_set_device_with_expected_argument_count() -> None:
    """set_device expects gwid, device_id, func, value after self."""
    method = _method_node("PanasonicFan", "async_set_preset_mode")
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and _is_self_client_set_device_call(node)]

    assert calls, "expected async_set_preset_mode to call self.client.set_device"
    assert all(len(call.args) == 4 for call in calls)
