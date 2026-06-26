"""Characterization tests for Panasonic command metadata parsing.

The production cloud module imports Home Assistant, which is not available in the
plain local Python test environment. These tests therefore execute only the
``_refactor_cmds_paras`` method extracted from source, using a redacted synthetic
CommandList fixture.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from tests.helpers.source_parsing import load_constant_assignments, load_method_function

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"
FIXTURE = ROOT / "tests" / "fixtures" / "command_list_pxgd_hdh_minimal.json"


class _DummyCloud:
    _commands_info: dict[str, Any]


def _load_parser() -> tuple[dict[str, Any], Callable[..., None]]:
    constants = load_constant_assignments(CONST_PATH)
    method = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="_refactor_cmds_paras",
        globals_env=constants,
    )
    return constants, method


def _parse_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    constants, parser = _load_parser()
    commands = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cloud = _DummyCloud()

    parser(cloud, copy.deepcopy(commands))

    return constants, cloud._commands_info


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
