"""P0 guard for writable climate entity descriptions missing set-command mappings."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"


def _literal_env() -> dict[str, object]:
    return load_constant_assignments(CONST_PATH)


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
