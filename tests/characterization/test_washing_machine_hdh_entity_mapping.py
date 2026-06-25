"""Characterize HDH washing-machine entity mapping against cloud metadata.

The user's NA-V160HDH cloud command list showed that 0x02 is not the HDH
course-setting command, 0x64 is the cloud course-setting command but still needs
separate characterization, 0x56 is a status/toggle-like value, and 0x61 is the
postpone-airing time setting.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from tests.helpers.source_parsing import load_constant_assignments
from tests.p0_known_bugs.test_climate_writable_descriptions_have_set_mappings import (
    _description_keys,
)

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"


def _constants() -> dict[str, object]:
    return load_constant_assignments(CONST_PATH)


def test_hdh_washer_does_not_expose_legacy_0x02_as_course_select() -> None:
    """HDH cloud metadata uses 0x64 for course setting; 0x02 is not in the list."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_SELECTS")

    assert const["WASHING_MACHINE_PROGRESS"] not in select_keys
    assert const["WASHING_MACHINE_PROGRESS_NEW"] not in select_keys


def test_postpone_airing_status_and_time_setting_are_not_conflated() -> None:
    """0x56 status/toggle and 0x61 time setting must be separate HA entities."""
    const = _constants()
    sensor_keys = _description_keys("WASHING_MACHINE_SENSORS")
    select_keys = _description_keys("WASHING_MACHINE_SELECTS")

    assert const["WASHING_MACHINE_POSTPONE_DRYING"] in sensor_keys
    assert const["WASHING_MACHINE_POSTPONE_DRYING"] not in select_keys
    assert const["WASHING_MACHINE_POSTPONE_DRYING_TIME"] in select_keys


def test_washer_status_polling_uses_cloud_hdh_keys_not_legacy_course_key() -> None:
    """The common washer polling list should include 0x56/0x61 but not legacy 0x02."""
    const = _constants()
    commands_type = cast(dict[str, list[str]], const["COMMANDS_TYPE"])
    washer_commands = commands_type[str(const["DEVICE_TYPE_WASHING_MACHINE"])]

    assert const["WASHING_MACHINE_PROGRESS"] not in washer_commands
    assert const["WASHING_MACHINE_POSTPONE_DRYING"] in washer_commands
    assert const["WASHING_MACHINE_POSTPONE_DRYING_TIME"] in washer_commands


def test_postpone_airing_time_uses_cloud_0x61_set_command() -> None:
    """The writable time-setting entity maps to the cloud 0x61 command."""
    const = _constants()
    set_commands = cast(
        dict[str, dict[str, int]],
        const["SET_COMMAND_TYPE"],
    )[str(const["DEVICE_TYPE_WASHING_MACHINE"])]

    assert cast(str, const["WASHING_MACHINE_POSTPONE_DRYING"]) not in set_commands
    assert set_commands[cast(str, const["WASHING_MACHINE_POSTPONE_DRYING_TIME"])] == int(
        cast(str, const["WASHING_MACHINE_61"]),
        16,
    )
