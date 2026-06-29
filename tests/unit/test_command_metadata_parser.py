"""Characterization tests for Panasonic command metadata parsing.

The production cloud module imports Home Assistant, which is not available in the
plain local Python test environment. These tests therefore execute only the
``_refactor_cmds_paras`` method extracted from source, using a redacted synthetic
CommandList fixture.
"""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
COMMAND_METADATA_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "command_metadata.py"
FIXTURE = ROOT / "tests" / "fixtures" / "command_list_pxgd_hdh_minimal.json"


def _load_constants() -> dict[str, Any]:
    constants = load_constant_assignments(CONST_PATH)
    return constants


def _load_refactor_command_metadata():
    spec = importlib.util.spec_from_file_location("panasonic_command_metadata", COMMAND_METADATA_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.refactor_command_metadata


def _parse_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    constants = _load_constants()
    refactor_command_metadata = _load_refactor_command_metadata()
    commands = json.loads(FIXTURE.read_text(encoding="utf-8"))
    original = json.loads(FIXTURE.read_text(encoding="utf-8"))

    parsed = refactor_command_metadata(
        commands,
        washing_machine_models=constants["WASHING_MACHINE_MODELS"],
        washing_machine_2020_models=constants["WASHING_MACHINE_2020_MODELS"],
        washing_machine_operating_status=constants["WASHING_MACHINE_OPERATING_STATUS"],
        washing_machine_timer_remaining_time=constants["WASHING_MACHINE_TIMER_REMAINING_TIME"],
    )

    assert commands == original, "parser must not mutate raw CommandList metadata"
    return constants, parsed


def test_command_metadata_parser_normalizes_command_type_names_and_device_type() -> None:
    _, parsed = _parse_fixture()
    pxgd = parsed["PXGD"][0]

    assert pxgd["DeviceType"] == "1"
    assert "list" not in pxgd
    assert "0x01" in pxgd["CommandParameters"]
    assert "0X01" not in pxgd["CommandParameters"]
    assert pxgd["CommandName"]["0x01"] == "運轉模式"


def test_command_metadata_parser_converts_enum_and_range_parameters() -> None:
    _, parsed = _parse_fixture()
    parameters = parsed["PXGD"][0]["CommandParameters"]

    assert parameters["0x01"] == {"Cool": 1, "Heat": 4}
    assert parameters["0x03"] == {str(value): value for value in range(16, 31)}


def test_command_metadata_parser_adds_auto_for_range_a_parameters() -> None:
    _, parsed = _parse_fixture()
    fan_speed = parsed["PXGD"][0]["CommandParameters"]["0x02"]

    assert fan_speed["Auto"] == 0
    assert fan_speed["1"] == 1
    assert fan_speed["5"] == 5


def test_washer_metadata_parser_adds_off_to_operating_status_enum() -> None:
    constants, parsed = _parse_fixture()
    operating_status = constants["WASHING_MACHINE_OPERATING_STATUS"]
    parameters = parsed["HDH"][0]["CommandParameters"][operating_status]

    assert parameters == {"Standby": 1, "Running": 2, "Off": 0}


def test_washer_metadata_parser_aliases_0x15_timer_to_remaining_time_key() -> None:
    constants, parsed = _parse_fixture()
    timer_remaining = constants["WASHING_MACHINE_TIMER_REMAINING_TIME"]
    hdh = parsed["HDH"][0]

    assert timer_remaining == "0x58"
    assert hdh["CommandParameters"][timer_remaining] == {
        str(value): value for value in range(0, 25)
    }
    assert hdh["CommandName"][timer_remaining] == "預約殘時間"
    assert hdh["CommandParameters"]["0x15"] == hdh["CommandParameters"][timer_remaining]


def test_command_metadata_parser_preserves_declared_command_type_order() -> None:
    constants, parsed = _parse_fixture()
    hdh = parsed["HDH"][0]

    assert hdh["CommandTypes"] == [
        constants["WASHING_MACHINE_OPERATING_STATUS"],
        "0x15",
    ]
