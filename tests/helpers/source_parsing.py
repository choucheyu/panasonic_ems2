"""AST utilities for tests that need to inspect Home Assistant-dependent modules."""

from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
import sys
import textwrap
import types
from pathlib import Path
from typing import Any, Callable


DESCRIPTION_MODULE_BY_PREFIX = {
    "AIRPURIFIER_": "airpurifier",
    "CLIMATE_": "climate",
    "DEHUMIDIFIER_": "dehumidifier",
    "DRYER_": "dryer",
    "ERV_": "erv",
    "FRIDGE_": "fridge",
    "LIGHT_": "light",
    "WASHING_MACHINE_": "washing_machine",
    "WEIGHT_PLATE_": "weight_plate",
}


def panasonic_description_source_path(core_path: Path, tuple_name: str) -> Path:
    """Return the source module that owns an appliance entity-description tuple."""
    for prefix, module_name in DESCRIPTION_MODULE_BY_PREFIX.items():
        if tuple_name.startswith(prefix):
            return core_path / "entity_descriptions" / f"{module_name}.py"
    return core_path / "const.py"


def eval_literalish(node: ast.AST, env: dict[str, Any]) -> Any:
    """Evaluate the small literal/name subset used by integration constants."""
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id not in env:
            raise KeyError(node.id)
        return env[node.id]

    if isinstance(node, ast.List):
        return [eval_literalish(item, env) for item in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(eval_literalish(item, env) for item in node.elts)

    if isinstance(node, ast.Set):
        return {eval_literalish(item, env) for item in node.elts}

    if isinstance(node, ast.Dict):
        parsed: dict[Any, Any] = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                raise TypeError("dictionary unpacking is not supported")
            parsed[eval_literalish(key, env)] = eval_literalish(value, env)
        return parsed

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "str" and len(node.args) == 1 and not node.keywords:
            return str(eval_literalish(node.args[0], env))

    raise TypeError(f"unsupported AST node for lightweight parsing: {ast.dump(node)}")


def _relative_import_path(path: Path, node: ast.ImportFrom) -> Path | None:
    """Resolve a relative import to a source file when possible."""
    if node.level < 1 or not node.module:
        return None

    base = path.parent
    for _ in range(node.level - 1):
        base = base.parent

    candidate = base / Path(*node.module.split("."))
    if candidate.with_suffix(".py").exists():
        return candidate.with_suffix(".py")
    if (candidate / "__init__.py").exists():
        return candidate / "__init__.py"
    return None


def load_constant_assignments(path: Path, _seen: set[Path] | None = None) -> dict[str, Any]:
    """Load literal-ish top-level assignments from a Python source file.

    Supports same-package relative imports used by ``core.const`` compatibility
    seams, so tests can keep reading legacy constants after safe decomposition.
    """
    path = path.resolve()
    seen = set(_seen or set())
    if path in seen:
        return {}
    seen.add(path)

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    env: dict[str, Any] = {}

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            import_path = _relative_import_path(path, node)
            if import_path is None:
                continue
            imported_env = load_constant_assignments(import_path, seen)
            for alias in node.names:
                if alias.name == "*":
                    env.update(imported_env)
                    continue
                if alias.name not in imported_env:
                    continue
                env[alias.asname or alias.name] = imported_env[alias.name]
            continue

        value_node: ast.AST | None = None
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
            value_node = node.value
        else:
            continue

        if not names:
            continue

        try:
            if value_node is None:
                continue
            value = eval_literalish(value_node, env)
        except (KeyError, TypeError):
            continue

        for name in names:
            env[name] = value

    return env


def load_method_function(
    path: Path,
    *,
    class_name: str,
    method_name: str,
    globals_env: dict[str, Any],
) -> Callable[..., Any]:
    """Extract and execute one method as a plain function from a class source file."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue

        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                segment = ast.get_source_segment(source, child)
                if segment is None:
                    raise LookupError(f"source segment not found for {class_name}.{method_name}")
                namespace = dict(globals_env)
                exec(textwrap.dedent(segment), namespace)
                return namespace[method_name]

    raise LookupError(f"{class_name}.{method_name} not found in {path}")


TEST_CORE_PACKAGE = "_panasonic_ems2_core_under_test"


def _ensure_synthetic_core_package(core_path: Path) -> None:
    """Create a synthetic package rooted at ``core_path`` for relative imports."""
    if TEST_CORE_PACKAGE in sys.modules:
        return
    module = types.ModuleType(TEST_CORE_PACKAGE)
    module.__package__ = TEST_CORE_PACKAGE
    module.__path__ = [str(core_path)]  # type: ignore[attr-defined]
    module.__spec__ = importlib.machinery.ModuleSpec(
        TEST_CORE_PACKAGE,
        loader=None,
        is_package=True,
    )
    sys.modules[TEST_CORE_PACKAGE] = module


def _load_core_module(module_name: str):
    """Load a core module without importing or faking the HA integration package."""
    repo_root = Path(__file__).resolve().parents[2]
    core_path = repo_root / "custom_components" / "panasonic_ems2" / "core"
    _ensure_synthetic_core_package(core_path)

    qualified_name = f"{TEST_CORE_PACKAGE}.{module_name}"
    if qualified_name in sys.modules:
        return sys.modules[qualified_name]

    module_path = core_path / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(
        qualified_name,
        module_path,
        submodule_search_locations=[str(module_path.parent)] if module_path.name == "__init__.py" else None,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load core module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


def add_capability_runtime_globals(env: dict[str, Any]) -> dict[str, Any]:
    """Add capability-registry/runtime helpers for extracted cloud methods."""
    capabilities = _load_core_module("capabilities")
    cloud_commands = _load_core_module("cloud_commands")
    cloud_status = _load_core_module("cloud_status")
    user_info_requests = _load_core_module("user_info_requests")

    climate = str(env["DEVICE_TYPE_CLIMATE"])
    runtime_env = dict(env)
    runtime_env.update(
        {
            "CAPABILITY_REGISTRY": capabilities.build_capability_registry(
                commands_type=env["COMMANDS_TYPE"],
                extra_commands=env["EXTRA_COMMANDS"],
                supplemental_commands=env["SUPPLEMENTAL_COMMANDS"],
                excess_commands=env["EXCESS_COMMANDS"],
                set_command_type=env["SET_COMMAND_TYPE"],
                range_family={climate: env["CLIMATE_RANGE_FAMILY"]},
                command_name_overrides=env["COMMAND_NAME_OVERRIDES"],
                command_range_overrides=env["COMMAND_RANGE_OVERRIDES"],
            ),
            "command_name_override": capabilities.command_name_override,
            "command_range_override": capabilities.command_range_override,
            "commands_for_model": capabilities.commands_for_model,
            "range_lookup_models": capabilities.range_lookup_models,
            "set_command_id": capabilities.set_command_id,
            "supplemental_commands_for_model": capabilities.supplemental_commands_for_model,
            "build_light_device_command_types": cloud_commands.build_light_device_command_types,
            "build_offline_information": cloud_status.build_offline_information,
            "build_polling_command_types": cloud_commands.build_polling_command_types,
            "filter_supplemental_snapshot": cloud_commands.filter_supplemental_snapshot,
            "build_user_info_statistics_requests": (
                user_info_requests.build_user_info_statistics_requests
            ),
            "get_supplemental_keys": cloud_commands.get_supplemental_keys,
            "merge_supplemental_status": cloud_commands.merge_supplemental_status,
            "normalize_command_status": cloud_status.normalize_command_status,
            "refactor_device_information": cloud_status.refactor_device_information,
        }
    )
    return runtime_env
