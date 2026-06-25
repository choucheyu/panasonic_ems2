"""P0 guard for writable climate entity descriptions missing set-command mappings."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"


def _literal_env() -> dict[str, object]:
    source = CONST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CONST_PATH))
    env: dict[str, object] = {}

    def eval_node(node: ast.AST) -> object:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return env[node.id]
        if isinstance(node, ast.Dict):
            return {eval_node(k): eval_node(v) for k, v in zip(node.keys, node.values) if k is not None}
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "str"
            and len(node.args) == 1
        ):
            return str(eval_node(node.args[0]))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -eval_node(node.operand)  # type: ignore[operator]
        raise TypeError(ast.dump(node))

    for node in tree.body:
        value = None
        names: list[str] = []
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
            value = node.value
        if not names or value is None:
            continue
        try:
            resolved = eval_node(value)
        except Exception:
            continue
        for name in names:
            env[name] = resolved
    return env


def _description_keys(tuple_name: str) -> list[str]:
    source = CONST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CONST_PATH))
    env = _literal_env()
    keys: list[str] = []
    for node in tree.body:
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == tuple_name:
            value = node.value
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == tuple_name for t in node.targets):
            value = node.value
        if value is None:
            continue
        for elt in value.elts:  # type: ignore[attr-defined]
            if not isinstance(elt, ast.Call):
                continue
            for kw in elt.keywords:
                if kw.arg == "key":
                    keys.append(env[ast.unparse(kw.value)])  # type: ignore[arg-type]
    return keys


def test_climate_writable_entity_descriptions_have_explicit_set_mappings() -> None:
    """Fail-closed set_device requires every writable climate entity to be mapped."""
    env = _literal_env()
    set_commands = env["SET_COMMAND_TYPE"][str(env["DEVICE_TYPE_CLIMATE"])]  # type: ignore[index]
    writable_keys = (
        _description_keys("CLIMATE_SWITCHES")
        + _description_keys("CLIMATE_SELECTS")
        + _description_keys("CLIMATE_NUMBERS")
    )

    # CLIMATE_FUZZY_MODE may appear only on models we do not currently own, but if
    # it is exposed by status in the future it still needs to preserve the legacy
    # write path after set_device became fail-closed.
    missing = sorted(key for key in writable_keys if key not in set_commands)

    assert missing == []
