"""Characterize HDH washing-machine entity mapping against observed cloud/app data.

The user's NA-V160HDH observations showed:

* 0x02 is a legacy/mirror status value for the current course, not the HDH
  course-setting command exposed by the cloud command list.
* 0x56 is not a confirmed 自動延後晾衣 toggle: it stayed 0 after the
  official app toggle was turned off while a pending program remained.
* 0x61 stayed 65535 while the official app delay-airing hour changed, so it
  must not be exposed as a writable 延後晾衣時間設定 control.
* 0x58 tracks the active completion-reservation countdown in minutes.
* 0x76 and 0x77 track detergent and softener ml settings respectively.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

from tests.helpers.source_parsing import load_constant_assignments
from tests.p0_known_bugs.test_climate_writable_descriptions_have_set_mappings import (
    _description_keys,
)

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"


def _constants() -> dict[str, object]:
    return load_constant_assignments(CONST_PATH)


def _hdh_main_polling_commands(const: dict[str, object]) -> list[str]:
    commands_type = cast(dict[str, list[str]], const["COMMANDS_TYPE"])
    extra_commands = cast(dict[str, dict[str, list[str]]], const["EXTRA_COMMANDS"])
    excess_commands = cast(dict[str, dict[str, list[str]]], const["EXCESS_COMMANDS"])
    washer_type = str(const["DEVICE_TYPE_WASHING_MACHINE"])
    base = commands_type[washer_type]
    extra = extra_commands[washer_type]["HDH"]
    excess = set(excess_commands[washer_type]["HDH"])

    return [command for command in base + extra if command not in excess]


def _eval_description_value(node: ast.AST, env: dict[str, object]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        value = _eval_description_value(node.value, env)
        return f"{value}.{node.attr}" if isinstance(value, str) else node.attr
    raise TypeError(ast.dump(node))


def _description_metadata(tuple_name: str) -> dict[str, dict[str, Any]]:
    source = CONST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CONST_PATH))
    env = _constants()
    descriptions: dict[str, dict[str, Any]] = {}

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
            metadata: dict[str, Any] = {}
            key = None
            for kw in elt.keywords:
                if kw.arg is None:
                    continue
                parsed = _eval_description_value(kw.value, env)
                metadata[kw.arg] = parsed
                if kw.arg == "key":
                    key = cast(str, parsed)
            if key is not None:
                descriptions[key] = metadata

    return descriptions


def test_hdh_washer_does_not_expose_legacy_or_composite_course_selects() -> None:
    """HDH course values 0x02/0x64 are observed/composite, not safe writable selects."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_SELECTS")

    assert const["WASHING_MACHINE_PROGRESS"] not in select_keys
    assert const["WASHING_MACHINE_PROGRESS_NEW"] not in select_keys


def test_observed_reservation_hour_is_read_only_sensor_not_writable_select() -> None:
    """0x14 read 15 for a pending completion reservation, outside the old 0..8 select."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_SELECTS")
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")
    set_commands = cast(
        dict[str, dict[str, int]],
        const["SET_COMMAND_TYPE"],
    )[str(const["DEVICE_TYPE_WASHING_MACHINE"])]

    assert const["WASHING_MACHINE_TIMER"] not in select_keys
    assert const["WASHING_MACHINE_TIMER"] not in set_commands
    reservation_hour = sensor_descriptions[cast(str, const["WASHING_MACHINE_TIMER"])]
    assert reservation_hour["name"] == "預約設定時間"
    assert reservation_hour["native_unit_of_measurement"] == "UnitOfTime.HOURS"


def test_unconfirmed_delay_airing_controls_are_not_exposed_as_writable_selects() -> None:
    """0x56 and 0x61 must not be presented as confirmed writable delay-airing controls."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_SELECTS")
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")

    assert const["WASHING_MACHINE_POSTPONE_DRYING"] not in select_keys
    assert const["WASHING_MACHINE_POSTPONE_DRYING_TIME"] not in select_keys
    assert const["WASHING_MACHINE_POSTPONE_DRYING"] in sensor_descriptions
    assert (
        sensor_descriptions[cast(str, const["WASHING_MACHINE_POSTPONE_DRYING"])]["name"]
        != "自動延後晾衣"
    )


def test_washer_status_polling_uses_remote_commandlist_keys() -> None:
    """HDH main polling follows the 12 commands advertised by the remote CommandList."""
    const = _constants()
    washer_commands = _hdh_main_polling_commands(const)

    expected_remote_commandlist = [
        const["WASHING_MACHINE_ENABLE"],
        const["WASHING_MACHINE_REMAING_WASH_TIME"],
        const["WASHING_MACHINE_TIMER"],
        const["WASHING_MACHINE_ERROR_CODE"],
        const["WASHING_MACHINE_OPERATING_STATUS"],
        const["WASHING_MACHINE_CURRENT_MODE"],
        const["WASHING_MACHINE_CURRENT_PROGRESS"],
        const["WASHING_MACHINE_WARM_WATER"],
        const["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"],
        const["WASHING_MACHINE_60"],
        const["WASHING_MACHINE_POSTPONE_DRYING_TIME"],
        const["WASHING_MACHINE_PROGRESS_NEW"],
    ]

    assert washer_commands == expected_remote_commandlist
    assert len(washer_commands) == 12


def test_hdh_observation_only_keys_are_supplemental_not_main_polling() -> None:
    """Confirmed non-CommandList keys are isolated like climate supplemental reads."""
    const = _constants()
    washer_type = str(const["DEVICE_TYPE_WASHING_MACHINE"])
    supplemental = cast(dict[str, dict[str, list[str]]], const["SUPPLEMENTAL_COMMANDS"])[washer_type]["HDH"]
    washer_commands = _hdh_main_polling_commands(const)

    expected_supplemental = [
        const["WASHING_MACHINE_TIMER_REMAINING_TIME"],
        const["WASHING_MACHINE_REMOTE_CONTROL"],
        const["WASHING_MACHINE_DETERGENT_AMOUNT"],
        const["WASHING_MACHINE_SOFTENER_AMOUNT"],
    ]

    assert supplemental == expected_supplemental
    assert set(supplemental).isdisjoint(washer_commands)


def test_uncertain_hdh_keys_stay_commented_with_traditional_chinese_rationale() -> None:
    """Unconfirmed keys must stay disabled until mapped to official app behavior."""
    source = CONST_PATH.read_text(encoding="utf-8")

    assert "以下 key 目前不是 HDH 遠端 CommandList 主包，且語意或穩定性尚未確認" in source
    assert "# WASHING_MACHINE_OPERATING_STATUS_OLD" in source
    assert "# WASHING_MACHINE_POSTPONE_DRYING" in source
    assert "# WASHING_MACHINE_53" in source
    assert "# WASHING_MACHINE_57" in source


def test_unconfirmed_delay_airing_time_has_no_set_command() -> None:
    """0x61 returned sentinel values and must not be writable until a real endpoint is found."""
    const = _constants()
    set_commands = cast(
        dict[str, dict[str, int]],
        const["SET_COMMAND_TYPE"],
    )[str(const["DEVICE_TYPE_WASHING_MACHINE"])]

    assert cast(str, const["WASHING_MACHINE_POSTPONE_DRYING"]) not in set_commands
    assert cast(str, const["WASHING_MACHINE_POSTPONE_DRYING_TIME"]) not in set_commands


def test_confirmed_detergent_and_softener_amount_sensors_use_ml() -> None:
    """Official app changes confirmed 0x76=detergent ml and 0x77=softener ml."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")

    detergent = sensor_descriptions[cast(str, const["WASHING_MACHINE_DETERGENT_AMOUNT"])]
    softener = sensor_descriptions[cast(str, const["WASHING_MACHINE_SOFTENER_AMOUNT"])]

    assert detergent["name"] == "洗劑投入設定"
    assert detergent["native_unit_of_measurement"] == "mL"
    assert softener["name"] == "柔軟劑投入設定"
    assert softener["native_unit_of_measurement"] == "mL"


def test_hdh_remote_commandlist_keys_have_readable_entities() -> None:
    """Every confirmed HDH main command is visible as a read-only sensor or a switch."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")
    switch_keys = set(_description_keys("WASHING_MACHINE_SWITCHES"))
    visible_keys = set(sensor_descriptions) | switch_keys

    assert set(_hdh_main_polling_commands(const)) <= visible_keys


def test_reservation_countdown_sensor_uses_observed_0x58_name() -> None:
    """0x58 tracked the active completion-reservation countdown in minutes."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")

    countdown = sensor_descriptions[cast(str, const["WASHING_MACHINE_TIMER_REMAINING_TIME"])]

    assert countdown["name"] == "預約完成剩餘時間"
    assert countdown["native_unit_of_measurement"] == "UnitOfTime.MINUTES"
