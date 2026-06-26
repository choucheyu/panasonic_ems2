"""Phase 5 guards for decomposing ``core/const.py`` safely.

The first safe slice moves climate command/capability definitions to a Home
Assistant-independent module while keeping the legacy ``core.const`` exports
available for existing runtime code and tests.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST = CORE / "const.py"
CLIMATE_CONSTANTS = CORE / "constants" / "climate.py"

CLIMATE_COMMAND_SYMBOLS = (
    "CLIMATE_POWER",
    "CLIMATE_OPERATING_MODE",
    "CLIMATE_FAN_SPEED",
    "CLIMATE_TARGET_TEMPERATURE",
    "CLIMATE_TEMPERATURE_INDOOR",
    "CLIMATE_PM25",
    "CLIMATE_MONITOR_MILDEW",
    "CLIMATE_IMMEDIATE_MILDEW_DRY",
    "CLIMATE_HUMIDITY_INDOOR",
    "CLIMATE_VOICE",
)

CLIMATE_CAPABILITY_SYMBOLS = (
    "CLIMATE_RX_COMMANDS",
    "CLIMATE_PXGD_SUPPLEMENTAL_COMMANDS",
    "CLIMATE_VX_SUPPLEMENTAL_COMMANDS",
    "CLIMATE_UX_SUPPLEMENTAL_COMMANDS",
    "CLIMATE_UJ_SUPPLEMENTAL_COMMANDS",
    "CLIMATE_UK_SUPPLEMENTAL_COMMANDS",
    "CLIMATE_PXGD_MODELS",
    "CLIMATE_PM25_MODELS",
    "CLIMATE_RANGE_FAMILY",
)


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _assignment_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_climate_constants_module_exists_and_is_plain_python() -> None:
    module = _load_module(CLIMATE_CONSTANTS, "panasonic_climate_constants_under_test")

    for symbol in CLIMATE_COMMAND_SYMBOLS + CLIMATE_CAPABILITY_SYMBOLS:
        assert hasattr(module, symbol)

    assert module.CLIMATE_POWER == "0x00"
    assert module.CLIMATE_VOICE == "0x59"
    assert module.CLIMATE_RANGE_FAMILY["UK"][module.CLIMATE_FAN_SPEED] == "PXGD"
    assert module.CLIMATE_OPERATING_MODE not in module.CLIMATE_RANGE_FAMILY["UK"]


def test_const_imports_climate_constants_without_redefining_command_tables() -> None:
    source = CONST.read_text(encoding="utf-8")
    assigned_names = _assignment_names(CONST)

    assert "from .constants.climate import" in source
    for symbol in CLIMATE_COMMAND_SYMBOLS + CLIMATE_CAPABILITY_SYMBOLS:
        assert symbol not in assigned_names

    # HA-specific preset mapping stays in const.py because it depends on HA climate constants.
    assert "CLIMATE_AVAILABLE_PRESET_MODES" in assigned_names


def test_legacy_const_exports_match_decomposed_climate_module() -> None:
    const_env = load_constant_assignments(CONST)
    climate_env = load_constant_assignments(CLIMATE_CONSTANTS)

    for symbol in CLIMATE_COMMAND_SYMBOLS + CLIMATE_CAPABILITY_SYMBOLS:
        assert const_env[symbol] == climate_env[symbol]

    assert const_env["CLIMATE_UX_SUPPLEMENTAL_COMMANDS"] == [
        const_env["CLIMATE_PM25"],
        const_env["CLIMATE_MONITOR_MILDEW"],
        const_env["CLIMATE_IMMEDIATE_MILDEW_DRY"],
        const_env["CLIMATE_VOICE"],
    ]


def test_high_risk_climate_rationales_move_with_the_climate_capabilities() -> None:
    source = CLIMATE_CONSTANTS.read_text(encoding="utf-8")

    assert "UX 官方有「室內溫濕度監控」" in source
    assert "待 UX cloud/status snapshot 確認後再啟用" in source
    assert "UJ 官方有「防霉監控」" in source
    assert "尚未確認是否等同 VX/UX 的 0x53 可寫開關" in source
    assert "UK/uk 官方有冷專與冷暖室外機差異" in source
    assert "避免冷專機型錯誤暴露「暖氣」" in source
