"""AST utilities for tests that need to inspect Home Assistant-dependent modules."""

from __future__ import annotations

import ast
import textwrap
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
