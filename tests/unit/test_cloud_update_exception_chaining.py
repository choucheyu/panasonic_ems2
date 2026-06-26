"""Guards for update-coordinator exception chaining."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLOUD = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"


def _cloud_method(method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    tree = ast.parse(CLOUD.read_text(encoding="utf-8"), filename=str(CLOUD))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PanasonicSmartHome":
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"PanasonicSmartHome.{method_name} not found")


def test_async_update_data_does_not_use_bare_except() -> None:
    method = _cloud_method("async_update_data")

    for node in ast.walk(method):
        if isinstance(node, ast.ExceptHandler):
            assert node.type is not None


def test_async_update_data_chains_update_failed_from_original_exception() -> None:
    method = _cloud_method("async_update_data")

    raises = [node for node in ast.walk(method) if isinstance(node, ast.Raise)]
    assert any(
        isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id == "UpdateFailed"
        and isinstance(node.cause, ast.Name)
        and node.cause.id == "err"
        for node in raises
    )
