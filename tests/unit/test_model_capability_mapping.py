"""Characterization tests for conservative climate model-family mappings.

These tests intentionally parse ``core/const.py`` with ``ast`` instead of importing it.
Plain local ``python3`` does not have Home Assistant installed, and Phase 0 should stay
lightweight and independent from a live HA shadow environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST_PATH = CORE_PATH / "const.py"
CLIMATE_CONSTANTS_PATH = CORE_PATH / "constants" / "climate.py"


def _load_const_assignments() -> dict[str, Any]:
    return load_constant_assignments(CONST_PATH)


def _climate_supplemental(env: dict[str, Any]) -> dict[str, list[str]]:
    climate_key = str(env["DEVICE_TYPE_CLIMATE"])
    return env["SUPPLEMENTAL_COMMANDS"][climate_key]


def _climate_extra_commands(env: dict[str, Any]) -> dict[str, list[str]]:
    climate_key = str(env["DEVICE_TYPE_CLIMATE"])
    return env["EXTRA_COMMANDS"][climate_key]


def test_vx_keeps_all_verified_supplemental_commands() -> None:
    env = _load_const_assignments()
    supplemental = _climate_supplemental(env)

    expected = {
        env["CLIMATE_PM25"],
        env["CLIMATE_MONITOR_MILDEW"],
        env["CLIMATE_IMMEDIATE_MILDEW_DRY"],
        env["CLIMATE_HUMIDITY_INDOOR"],
        env["CLIMATE_VOICE"],
    }

    assert set(supplemental["VX"]) == expected


def test_ux_uses_vx_like_supplemental_commands_without_unverified_humidity() -> None:
    env = _load_const_assignments()
    supplemental = _climate_supplemental(env)

    expected = {
        env["CLIMATE_PM25"],
        env["CLIMATE_MONITOR_MILDEW"],
        env["CLIMATE_IMMEDIATE_MILDEW_DRY"],
        env["CLIMATE_VOICE"],
    }

    assert set(supplemental["UX"]) == expected
    assert env["CLIMATE_HUMIDITY_INDOOR"] not in supplemental["UX"]


def test_uxfa_aliases_existing_ux_family_without_unverified_humidity() -> None:
    env = _load_const_assignments()
    supplemental = _climate_supplemental(env)
    extra_commands = _climate_extra_commands(env)
    range_family = env["CLIMATE_RANGE_FAMILY"]
    operating_mode = env["CLIMATE_OPERATING_MODE"]
    fan_speed = env["CLIMATE_FAN_SPEED"]

    assert extra_commands["UXFA"] == extra_commands["UX"]
    assert supplemental["UXFA"] == supplemental["UX"]
    assert env["CLIMATE_HUMIDITY_INDOOR"] not in supplemental["UXFA"]
    assert "UXFA" in env["CLIMATE_PXGD_MODELS"]
    assert "UXFA" in env["CLIMATE_PM25_MODELS"]
    assert range_family["UXFA"][operating_mode] == "PXGD"
    assert range_family["UXFA"][fan_speed] == "PXGD"


def test_uj_and_uk_keep_high_risk_supplemental_commands_disabled() -> None:
    env = _load_const_assignments()
    supplemental = _climate_supplemental(env)
    high_risk = {
        env["CLIMATE_PM25"],
        env["CLIMATE_MONITOR_MILDEW"],
        env["CLIMATE_IMMEDIATE_MILDEW_DRY"],
        env["CLIMATE_HUMIDITY_INDOOR"],
        env["CLIMATE_VOICE"],
    }

    for model_type in ("UJ", "UK", "uk"):
        assert supplemental[model_type] == []
        assert high_risk.isdisjoint(supplemental[model_type])


def test_range_fallbacks_match_conservative_model_family_design() -> None:
    env = _load_const_assignments()
    range_family = env["CLIMATE_RANGE_FAMILY"]
    operating_mode = env["CLIMATE_OPERATING_MODE"]
    fan_speed = env["CLIMATE_FAN_SPEED"]

    for model_type in ("VX", "UX", "UJ"):
        assert range_family[model_type][operating_mode] == "PXGD"
        assert range_family[model_type][fan_speed] == "PXGD"

    for model_type in ("UK", "uk"):
        assert operating_mode not in range_family[model_type]
        assert range_family[model_type][fan_speed] == "PXGD"


def test_new_model_types_are_registered_but_pm25_remains_conservative() -> None:
    env = _load_const_assignments()
    extra_commands = _climate_extra_commands(env)
    pxgd_family = set(env["CLIMATE_PXGD_MODELS"])
    pm25_models = set(env["CLIMATE_PM25_MODELS"])

    assert {"VX", "UX", "UXFA", "UJ", "UK", "uk"}.issubset(extra_commands)
    assert {"VX", "UX", "UXFA", "UJ", "UK", "uk"}.issubset(pxgd_family)

    assert {"VX", "UX", "UXFA"}.issubset(pm25_models)
    assert "UJ" not in pm25_models
    assert "UK" not in pm25_models
    assert "uk" not in pm25_models


def test_disabled_high_risk_capabilities_have_traditional_chinese_rationale() -> None:
    source = CLIMATE_CONSTANTS_PATH.read_text(encoding="utf-8")

    assert "UX 官方有「室內溫濕度監控」" in source
    assert "待 UX cloud/status snapshot 確認後再啟用" in source
    assert "UJ 官方有「防霉監控」" in source
    assert "尚未確認是否等同 VX/UX 的 0x53 可寫開關" in source
    assert "UK/uk 官方有冷專與冷暖室外機差異" in source
    assert "避免冷專機型錯誤暴露「暖氣」" in source
