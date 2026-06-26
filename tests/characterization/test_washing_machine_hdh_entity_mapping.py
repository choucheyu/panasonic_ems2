"""Characterize HDH washing-machine entity mapping against observed cloud/app data.

The user's NA-V160HDH observations showed:

* 0x02 is a legacy/mirror status value for the current course, not the HDH
  course-setting command exposed by the cloud command list.
* 0x56 is not a confirmed 自動延後晾衣 toggle: it stayed 0 after the
  official app toggle was turned off while a pending program remained.
* 0x61 is the CommandList-backed 延後晾衣設定 key; 0x56 remains the legacy/raw
  observation key and must not be exposed as the setting select.
* 0x58 tracks the active completion/finish estimate in minutes.
* 0x76 and 0x77 track detergent and softener ml settings respectively.
"""

from __future__ import annotations

import ast
from types import SimpleNamespace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

from tests.helpers.source_parsing import (
    add_capability_runtime_globals,
    load_constant_assignments,
    load_method_function,
    panasonic_description_source_path,
)
from tests.p0_known_bugs.test_climate_writable_descriptions_have_set_mappings import (
    _description_keys,
)

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST_PATH = CORE_PATH / "const.py"
WASHING_MACHINE_CONSTANTS_PATH = CORE_PATH / "constants" / "washing_machine.py"
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"
SENSOR_PATH = ROOT / "custom_components" / "panasonic_ems2" / "sensor.py"


def _constants() -> dict[str, object]:
    return add_capability_runtime_globals(load_constant_assignments(CONST_PATH))


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
    source_path = panasonic_description_source_path(CORE_PATH, tuple_name)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
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


def test_hdh_washer_exposes_commandlist_course_select_not_legacy_course_select() -> None:
    """HDH uses CommandList 0x64 as course select; legacy 0x02 remains out."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_HDH_SELECTS")

    assert const["WASHING_MACHINE_PROGRESS"] not in select_keys
    assert const["WASHING_MACHINE_PROGRESS_NEW"] in select_keys


def test_hdh_commandlist_setting_keys_are_exposed_as_select_candidates() -> None:
    """Expose HDH CommandList-backed settings as selects; keep legacy 0x02 out."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_HDH_SELECTS")
    set_commands = cast(
        dict[str, dict[str, int]],
        const["SET_COMMAND_TYPE"],
    )[str(const["DEVICE_TYPE_WASHING_MACHINE"])]

    assert select_keys == [
        const["WASHING_MACHINE_TIMER"],
        const["WASHING_MACHINE_60"],
        const["WASHING_MACHINE_POSTPONE_DRYING_TIME"],
        const["WASHING_MACHINE_PROGRESS_NEW"],
    ]
    assert const["WASHING_MACHINE_PROGRESS"] not in select_keys
    for key in select_keys:
        assert key in set_commands


def test_legacy_delay_airing_raw_key_is_not_exposed_as_writable_select() -> None:
    """0x56 stays raw/read-only; 0x61 is the CommandList-backed setting select."""
    const = _constants()
    select_keys = _description_keys("WASHING_MACHINE_HDH_SELECTS")
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")

    assert const["WASHING_MACHINE_POSTPONE_DRYING"] not in select_keys
    assert const["WASHING_MACHINE_POSTPONE_DRYING_TIME"] in select_keys
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
        const["WASHING_MACHINE_ENERGY"],
        const["WASHING_MACHINE_REMOTE_CONTROL"],
        const["WASHING_MACHINE_DETERGENT_AMOUNT"],
        const["WASHING_MACHINE_SOFTENER_AMOUNT"],
    ]

    assert supplemental == expected_supplemental
    assert set(supplemental).isdisjoint(washer_commands)


def test_hdh_supplemental_display_keys_include_monthly_energy_and_update_status() -> None:
    """Display-only supplemental keys include UserGetInfo/UpdateCheck values without DeviceGetInfo polling."""
    const = _constants()
    washer_type = str(const["DEVICE_TYPE_WASHING_MACHINE"])
    device_get_info_supplemental = cast(
        dict[str, dict[str, list[str]]],
        const["SUPPLEMENTAL_COMMANDS"],
    )[washer_type]["HDH"]

    display_supplemental = const["WASHING_MACHINE_HDH_SUPPLEMENTAL_DISPLAY_KEYS"]

    assert display_supplemental == [
        const["WASHING_MACHINE_TIMER_REMAINING_TIME"],
        const["WASHING_MACHINE_ENERGY"],
        const["WASHING_MACHINE_REMOTE_CONTROL"],
        const["WASHING_MACHINE_DETERGENT_AMOUNT"],
        const["WASHING_MACHINE_SOFTENER_AMOUNT"],
        const["ENTITY_WATER_USED"],
        const["ENTITY_WASH_TIMES"],
        const["ENTITY_UPDATE"],
    ]
    assert const["ENTITY_WATER_USED"] not in device_get_info_supplemental
    assert const["ENTITY_WASH_TIMES"] not in device_get_info_supplemental
    assert const["ENTITY_UPDATE"] not in device_get_info_supplemental


def test_uncertain_hdh_keys_stay_commented_with_traditional_chinese_rationale() -> None:
    """Unconfirmed keys must stay disabled until mapped to official app behavior."""
    source = WASHING_MACHINE_CONSTANTS_PATH.read_text(encoding="utf-8")

    assert "以下 key 目前不是 HDH 遠端 CommandList 主包，且語意或穩定性尚未確認" in source
    assert "# WASHING_MACHINE_OPERATING_STATUS_OLD" in source
    assert "# WASHING_MACHINE_POSTPONE_DRYING" in source
    assert "# WASHING_MACHINE_53" in source
    assert "# WASHING_MACHINE_57" in source


def test_legacy_delay_airing_raw_key_has_no_set_command_but_0x61_does() -> None:
    """0x56 stays raw-only; 0x61 is the CommandList-backed writable setting."""
    const = _constants()
    set_commands = cast(
        dict[str, dict[str, int]],
        const["SET_COMMAND_TYPE"],
    )[str(const["DEVICE_TYPE_WASHING_MACHINE"])]

    assert cast(str, const["WASHING_MACHINE_POSTPONE_DRYING"]) not in set_commands
    assert cast(str, const["WASHING_MACHINE_POSTPONE_DRYING_TIME"]) in set_commands


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


def test_hdh_main_command_labels_match_remote_commandlist_chinese() -> None:
    """Main-polling labels use the user-facing Traditional Chinese names."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")
    switch_descriptions = _description_metadata("WASHING_MACHINE_SWITCHES")

    labels = {
        key: metadata["name"]
        for key, metadata in {**sensor_descriptions, **switch_descriptions}.items()
    }

    expected = {
        const["WASHING_MACHINE_ENABLE"]: "開始洗衣",
        const["WASHING_MACHINE_REMAING_WASH_TIME"]: "預估洗衣完成時間",
        const["WASHING_MACHINE_TIMER"]: "預約時間設定",
        const["WASHING_MACHINE_ERROR_CODE"]: "異常代碼",
        const["WASHING_MACHINE_OPERATING_STATUS"]: "運轉情報",
        const["WASHING_MACHINE_CURRENT_MODE"]: "目前洗衣行程",
        const["WASHING_MACHINE_CURRENT_PROGRESS"]: "洗衣行程設定",
        const["WASHING_MACHINE_WARM_WATER"]: "溫水設定",
        const["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"]: "預約洗衣開始時間",
        const["WASHING_MACHINE_60"]: "時間調整",
        const["WASHING_MACHINE_POSTPONE_DRYING_TIME"]: "延後晾衣設定",
        const["WASHING_MACHINE_PROGRESS_NEW"]: "行程設定",
    }

    assert {key: labels[key] for key in _hdh_main_polling_commands(const)} == expected


def test_command_name_overrides_win_over_remote_commandlist_names() -> None:
    """Entity names must honor local overrides even when Panasonic metadata has older names."""
    const = _constants()
    get_command_name = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="get_command_name",
        globals_env=const,
    )

    class Client:
        _devices_info = {
            "GWID_TEST": {
                "ModelType": "HDH",
                "DeviceType": str(const["DEVICE_TYPE_WASHING_MACHINE"]),
            }
        }
        _commands_info = {
            "HDH": [
                {
                    "DeviceType": str(const["DEVICE_TYPE_WASHING_MACHINE"]),
                    "CommandName": {
                        const["WASHING_MACHINE_REMAING_WASH_TIME"]: "洗衣殘時間",
                        const["WASHING_MACHINE_CURRENT_MODE"]: "工程訊息",
                        const["WASHING_MACHINE_CURRENT_PROGRESS"]: "行程別訊息",
                        const["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"]: "預約殘時間",
                    },
                }
            ]
        }

    client = Client()

    assert get_command_name(client, "GWID_TEST", const["WASHING_MACHINE_REMAING_WASH_TIME"]) == "預估洗衣完成時間"
    assert get_command_name(client, "GWID_TEST", const["WASHING_MACHINE_CURRENT_MODE"]) == "目前洗衣行程"
    assert get_command_name(client, "GWID_TEST", const["WASHING_MACHINE_CURRENT_PROGRESS"]) == "洗衣行程設定"
    assert get_command_name(client, "GWID_TEST", const["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"]) == "預約洗衣開始時間"
    assert get_command_name(client, "GWID_TEST", const["WASHING_MACHINE_TIMER_REMAINING_TIME"]) == "預約洗衣完成時間"
    assert get_command_name(client, "GWID_TEST", const["WASHING_MACHINE_REMOTE_CONTROL"]) == "遠端遙控"


def test_remote_control_value_uses_local_open_closed_mapping() -> None:
    """0x74 raw 1/0 should render as 開啟/關閉, not as raw numbers."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")
    remote = sensor_descriptions[cast(str, const["WASHING_MACHINE_REMOTE_CONTROL"])]

    assert remote["name"] == "遠端遙控"
    assert remote["device_class"] == "SensorDeviceClass.ENUM"
    assert const["COMMAND_RANGE_OVERRIDES"] == {
        str(const["DEVICE_TYPE_WASHING_MACHINE"]): {
            const["WASHING_MACHINE_REMOTE_CONTROL"]: {
                "關閉": 0,
                "開啟": 1,
            }
        }
    }

    get_range = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="get_range",
        globals_env=const,
    )

    class Client:
        _devices_info = {
            "GWID_TEST": {
                "ModelType": "HDH",
                "DeviceType": str(const["DEVICE_TYPE_WASHING_MACHINE"]),
            }
        }
        _commands_info = {}

    assert get_range(Client(), "GWID_TEST", const["WASHING_MACHINE_REMOTE_CONTROL"]) == {
        "關閉": 0,
        "開啟": 1,
    }


def test_reservation_countdown_sensor_uses_observed_0x58_name() -> None:
    """0x58 is the reservation finish estimate, not the active running finish estimate."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")

    countdown = sensor_descriptions[cast(str, const["WASHING_MACHINE_TIMER_REMAINING_TIME"])]

    assert countdown["name"] == "預約洗衣完成時間"


def test_monthly_user_info_labels_use_current_month_wording() -> None:
    """0xA2/0xA3 are current-month UserGetInfo values, not generic monthly labels."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")

    water = sensor_descriptions[cast(str, const["ENTITY_WATER_USED"])]
    wash_times = sensor_descriptions[cast(str, const["ENTITY_WASH_TIMES"])]

    assert water["name"] == "當月用水量"
    assert wash_times["name"] == "當月洗衣次數"


def test_washer_clock_time_keys_follow_operating_status_semantics() -> None:
    """0x13 is active-running only; 0x15/0x58 are reservation-only clock estimates."""
    const = _constants()
    sensor_descriptions = _description_metadata("WASHING_MACHINE_SENSORS")
    time_keys = [
        const["WASHING_MACHINE_REMAING_WASH_TIME"],
        const["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"],
        const["WASHING_MACHINE_TIMER_REMAINING_TIME"],
    ]

    for key in time_keys:
        description = sensor_descriptions[cast(str, key)]
        assert "native_unit_of_measurement" not in description
        assert "state_class" not in description

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 26, 10, 58)

    sensor_device_class = SimpleNamespace(
        ENUM="SensorDeviceClass.ENUM",
        TEMPERATURE="SensorDeviceClass.TEMPERATURE",
        HUMIDITY="SensorDeviceClass.HUMIDITY",
        ENERGY="SensorDeviceClass.ENERGY",
    )
    native_value = load_method_function(
        SENSOR_PATH,
        class_name="PanasonicSensor",
        method_name="native_value",
        globals_env={
            **const,
            "SensorDeviceClass": sensor_device_class,
            "datetime": FixedDateTime,
            "timedelta": timedelta,
        },
    )

    class Sensor:
        coordinator = SimpleNamespace(data={})
        info = {"DeviceType": const["DEVICE_TYPE_WASHING_MACHINE"]}

        def __init__(self, key: str, value: int, operating_status: int) -> None:
            self.key = key
            self.value = value
            self.operating_status = operating_status
            self.entity_description = SimpleNamespace(key=key, device_class=None)

        def get_status(self, _data: object) -> dict[str, int]:
            operating_status_key = cast(str, const["WASHING_MACHINE_OPERATING_STATUS"])
            return {
                self.key: self.value,
                operating_status_key: self.operating_status,
            }

    active_finish_key = cast(str, const["WASHING_MACHINE_REMAING_WASH_TIME"])
    reservation_start_key = cast(str, const["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"])
    reservation_finish_key = cast(str, const["WASHING_MACHINE_TIMER_REMAINING_TIME"])

    assert native_value(Sensor(active_finish_key, 35, 2)) == "11:33"
    assert native_value(Sensor(active_finish_key, 35, 3)) is None
    assert native_value(Sensor(active_finish_key, 35, 4)) is None
    assert native_value(Sensor(active_finish_key, 35, 1)) is None

    for key in [reservation_start_key, reservation_finish_key]:
        assert native_value(Sensor(key, 35, 3)) == "11:33"
        assert native_value(Sensor(key, 35, 4)) == "11:33"
        assert native_value(Sensor(key, 35, 2)) is None
        assert native_value(Sensor(key, 35, 1)) is None
        assert native_value(Sensor(key, 64933, 3)) is None


def test_finish_estimate_suppresses_panasonic_sentinel_values() -> None:
    """0x58 returned 64933 once washing started; do not show it as real minutes."""
    const = _constants()
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 26, 10, 58)

    sensor_device_class = SimpleNamespace(
        ENUM="SensorDeviceClass.ENUM",
        TEMPERATURE="SensorDeviceClass.TEMPERATURE",
        HUMIDITY="SensorDeviceClass.HUMIDITY",
        ENERGY="SensorDeviceClass.ENERGY",
    )
    native_value = load_method_function(
        SENSOR_PATH,
        class_name="PanasonicSensor",
        method_name="native_value",
        globals_env={
            **const,
            "SensorDeviceClass": sensor_device_class,
            "datetime": FixedDateTime,
            "timedelta": timedelta,
        },
    )

    class Sensor:
        entity_description = SimpleNamespace(
            key=const["WASHING_MACHINE_TIMER_REMAINING_TIME"],
            device_class=None,
        )
        coordinator = SimpleNamespace(data={})
        info = {"DeviceType": const["DEVICE_TYPE_WASHING_MACHINE"]}
        operating_status = 3

        def __init__(self, value: int) -> None:
            self.value = value

        def get_status(self, _data: object) -> dict[str, int]:
            key = cast(str, const["WASHING_MACHINE_TIMER_REMAINING_TIME"])
            operating_status_key = cast(str, const["WASHING_MACHINE_OPERATING_STATUS"])
            return {
                key: self.value,
                operating_status_key: self.operating_status,
            }

    Sensor.operating_status = 3
    assert native_value(Sensor(64933)) is None
    assert native_value(Sensor(65535)) is None
    assert native_value(Sensor(123)) == "13:01"

    Sensor.operating_status = 2
    assert native_value(Sensor(123)) is None
