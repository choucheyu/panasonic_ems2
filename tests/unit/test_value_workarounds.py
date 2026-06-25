"""Characterization tests for cloud status value workarounds.

The production cloud module imports Home Assistant, which is not available in the
plain local Python test environment. These tests therefore execute the single
``_workaround_info`` method extracted from source with the real constants loaded
from ``core/const.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tests.helpers.source_parsing import load_constant_assignments, load_method_function

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"


def _load_workaround() -> tuple[dict[str, Any], Callable[..., tuple[str, Any]]]:
    constants = load_constant_assignments(CONST_PATH)
    method = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="_workaround_info",
        globals_env=constants,
    )
    return constants, method


def test_vx_and_ux_pm25_invalid_value_is_normalized_to_minus_one() -> None:
    constants, workaround = _load_workaround()
    pm25 = constants["CLIMATE_PM25"]

    for model_type in ("VX", "UX"):
        command_type, value = workaround(None, model_type, pm25, 65535)
        assert command_type == pm25
        assert value == -1

        command_type, value = workaround(None, model_type, pm25, "65535")
        assert command_type == pm25
        assert value == -1


def test_pm25_invalid_value_is_not_applied_to_unverified_climate_families() -> None:
    constants, workaround = _load_workaround()
    pm25 = constants["CLIMATE_PM25"]

    for model_type in ("PXGD", "UJ", "UK", "uk"):
        command_type, value = workaround(None, model_type, pm25, 65535)
        assert command_type == pm25
        assert value == 65535


def test_pm25_normal_values_are_left_as_integers_for_vx_and_ux() -> None:
    constants, workaround = _load_workaround()
    pm25 = constants["CLIMATE_PM25"]

    for model_type in ("VX", "UX"):
        command_type, value = workaround(None, model_type, pm25, "12")
        assert command_type == pm25
        assert value == 12


def test_washing_machine_large_remaining_time_is_clamped_to_zero() -> None:
    constants, workaround = _load_workaround()
    remaining_time = constants["WASHING_MACHINE_TIMER_REMAINING_TIME"]

    for model_type in ("HDH", "KBS", "LMS", "LM", "DDH", "MDH", "DW", "LX128B"):
        command_type, value = workaround(None, model_type, remaining_time, 65001)
        assert command_type == remaining_time
        assert value == 0


def test_washing_machine_normal_remaining_time_is_left_as_integer() -> None:
    constants, workaround = _load_workaround()
    remaining_time = constants["WASHING_MACHINE_TIMER_REMAINING_TIME"]

    command_type, value = workaround(None, "HDH", remaining_time, "42")
    assert command_type == remaining_time
    assert value == 42


def test_xgs_fridge_temperature_values_use_existing_minus_255_adjustment() -> None:
    constants, workaround = _load_workaround()

    for key_name in ("FRIDGE_FREEZER_TEMPERATURE", "FRIDGE_THAW_TEMPERATURE"):
        command = constants[key_name]
        command_type, value = workaround(None, "XGS", command, 260)
        assert command_type == command
        assert value == 5


def test_dehumidifier_pm25_invalid_value_is_normalized_for_existing_families() -> None:
    constants, workaround = _load_workaround()
    pm25 = constants["DEHUMIDIFIER_PM25"]

    for model_type in ("GXW", "JHW"):
        command_type, value = workaround(None, model_type, pm25, 65535)
        assert command_type == pm25
        assert value == -1


def test_unparseable_status_falls_back_to_original_value() -> None:
    constants, workaround = _load_workaround()
    pm25 = constants["CLIMATE_PM25"]

    command_type, value = workaround(None, "VX", pm25, "not-a-number")
    assert command_type == pm25
    assert value == "not-a-number"
