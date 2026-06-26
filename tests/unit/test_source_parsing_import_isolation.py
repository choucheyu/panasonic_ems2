"""Guards for plain-Python source parsing helper import isolation."""

from __future__ import annotations

import sys
from pathlib import Path

from tests.helpers.source_parsing import (
    add_capability_runtime_globals,
    load_constant_assignments,
)

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
REAL_PACKAGE_NAMES = (
    "custom_components",
    "custom_components.panasonic_ems2",
    "custom_components.panasonic_ems2.core",
)


def test_runtime_globals_do_not_install_fake_real_integration_packages(monkeypatch) -> None:
    """Source parsing helpers must not poison real integration package names."""
    for name in list(sys.modules):
        if name in REAL_PACKAGE_NAMES or name.startswith("custom_components.panasonic_ems2.core"):
            monkeypatch.delitem(sys.modules, name, raising=False)

    env = load_constant_assignments(CONST_PATH)
    runtime_env = add_capability_runtime_globals(env)

    assert runtime_env["CAPABILITY_REGISTRY"]
    for name in REAL_PACKAGE_NAMES:
        assert name not in sys.modules
