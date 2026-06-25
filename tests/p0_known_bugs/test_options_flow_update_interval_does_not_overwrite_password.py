"""P0 guard for the options-flow password/update-interval bug."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FLOW_PATH = ROOT / "custom_components" / "panasonic_ems2" / "config_flow.py"


def _method_node(class_name: str, method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    tree = ast.parse(CONFIG_FLOW_PATH.read_text(encoding="utf-8"), filename=str(CONFIG_FLOW_PATH))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"{class_name}.{method_name} not found")


def _assigns_self_attr_from_name(node: ast.AST, *, attr_name: str, source_name: str) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Assign):
            continue
        for target in child.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == attr_name
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                if source_name in ast.unparse(child.value):
                    return True
    return False


@pytest.mark.p0_bug
def test_options_flow_update_interval_does_not_overwrite_password() -> None:
    """Changing update interval must update _update_interval, never _password."""
    method = _method_node("OptionsFlowHandler", "async_step_init")

    assert not _assigns_self_attr_from_name(
        method,
        attr_name="_password",
        source_name="CONF_UPDATE_INTERVAL",
    )
    assert _assigns_self_attr_from_name(
        method,
        attr_name="_update_interval",
        source_name="CONF_UPDATE_INTERVAL",
    )
