"""Phase 7 guards for decomposing ``core/cloud.py`` helper logic."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "custom_components" / "panasonic_ems2" / "core"
CLOUD = CORE / "cloud.py"

EXPECTED_HELPER_MODULES = {
    "cloud_commands.py": {
        "build_polling_command_types",
        "build_light_device_command_types",
        "get_supplemental_keys",
        "merge_supplemental_status",
    },
    "cloud_status.py": {
        "normalize_command_status",
        "refactor_device_information",
        "build_offline_information",
    },
    "user_info_requests.py": {
        "build_user_info_statistics_requests",
    },
}

THIN_CLOUD_METHOD_LIMITS = {
    "_workaround_info": 4,
    "_refactor_info": 4,
    "_get_supplemental_keys": 4,
    "_merge_supplemental_status": 4,
    "_get_commands": 12,
    "_get_device_commands": 8,
    "_offline_info": 8,
    "_user_info_statistics_requests": 4,
}


def _cloud_class() -> ast.ClassDef:
    tree = ast.parse(CLOUD.read_text(encoding="utf-8"), filename=str(CLOUD))
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PanasonicSmartHome"
    )


def test_cloud_decomposition_helper_modules_exist_with_expected_functions() -> None:
    for file_name, function_names in EXPECTED_HELPER_MODULES.items():
        path = CORE / file_name
        assert path.exists(), f"missing {file_name}"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert function_names <= functions


def test_cloud_imports_decomposed_helper_modules() -> None:
    tree = ast.parse(CLOUD.read_text(encoding="utf-8"), filename=str(CLOUD))
    imported_modules = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1
    }

    assert "cloud_commands" in imported_modules
    assert "cloud_status" in imported_modules
    assert "user_info_requests" in imported_modules


def test_cloud_helper_methods_are_thin_delegation_wrappers() -> None:
    methods = {
        node.name: node
        for node in _cloud_class().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    for method_name, max_lines in THIN_CLOUD_METHOD_LIMITS.items():
        method = methods[method_name]
        assert method.end_lineno is not None
        assert method.end_lineno - method.lineno + 1 <= max_lines, method_name


def test_cloud_py_line_count_stays_below_phase7_budget() -> None:
    assert len(CLOUD.read_text(encoding="utf-8").splitlines()) <= 1050
