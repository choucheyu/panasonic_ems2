"""Regression guards for scoped Panasonic CommandList polling.

Cloud-declared CommandList metadata is useful for washer/dryer model support, but
it must not shrink climate polling. Panasonic climate CommandList is not a full
entity/status declaration, and treating it as one breaks existing PXGD/VX climate
sensors, selects, switches, and numbers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import (
    add_capability_runtime_globals,
    load_constant_assignments,
    load_method_function,
)

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "custom_components" / "panasonic_ems2" / "core"
CONST_PATH = CORE / "const.py"
CLOUD_PATH = CORE / "cloud.py"
SENSOR_PLATFORM_PATH = ROOT / "custom_components" / "panasonic_ems2" / "sensor.py"
WASHER_DESCRIPTIONS_PATH = CORE / "entity_descriptions" / "washing_machine.py"
DRYER_DESCRIPTIONS_PATH = CORE / "entity_descriptions" / "dryer.py"


def _runtime_env() -> dict[str, Any]:
    return add_capability_runtime_globals(load_constant_assignments(CONST_PATH))


def _command_type_values(payload: list[dict[str, str]]) -> list[str]:
    return [item["CommandType"] for item in payload]


def _source_contains(path: Path, *needles: str) -> None:
    source = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in source


def test_declared_commandlist_polling_is_scoped_to_washer_and_dryer() -> None:
    env = _runtime_env()
    declared_device_types = (
        env["DEVICE_TYPE_WASHING_MACHINE"],
        env["DEVICE_TYPE_DRYER"],
    )

    washer_declared = [
        env["WASHING_MACHINE_CURRENT_PROGRESS"],
        env["WASHING_MACHINE_OPERATING_STATUS"],
        env["WASHING_MACHINE_CURRENT_MODE"],
    ]
    dryer_declared = [
        env["DRYER_PROGRAM_1"],
        env["DRYER_PROGRAM_2"],
    ]
    climate_declared = [
        env["CLIMATE_POWER"],
        env["CLIMATE_OPERATING_MODE"],
        env["CLIMATE_TARGET_TEMPERATURE"],
    ]

    washer_payload = env["build_polling_command_types"](
        env["DEVICE_TYPE_WASHING_MACHINE"],
        "DSH",
        has_remote_commands=True,
        remote_command_types=washer_declared,
        declared_command_device_types=declared_device_types,
        capability_registry=env["CAPABILITY_REGISTRY"],
        model_jp_types=env["MODEL_JP_TYPES"],
    )
    dryer_payload = env["build_polling_command_types"](
        env["DEVICE_TYPE_DRYER"],
        "CN-HP",
        has_remote_commands=True,
        remote_command_types=dryer_declared,
        declared_command_device_types=declared_device_types,
        capability_registry=env["CAPABILITY_REGISTRY"],
        model_jp_types=env["MODEL_JP_TYPES"],
    )
    climate_payload = env["build_polling_command_types"](
        env["DEVICE_TYPE_CLIMATE"],
        "PXGD",
        has_remote_commands=True,
        remote_command_types=climate_declared,
        declared_command_device_types=declared_device_types,
        capability_registry=env["CAPABILITY_REGISTRY"],
        model_jp_types=env["MODEL_JP_TYPES"],
    )

    assert _command_type_values(washer_payload) == washer_declared
    assert _command_type_values(dryer_payload) == dryer_declared

    climate_commands = _command_type_values(climate_payload)
    assert climate_commands != climate_declared
    for required_key in (
        env["CLIMATE_TEMPERATURE_INDOOR"],
        env["CLIMATE_AIRFRESH_MODE"],
        env["CLIMATE_TIMER_ON"],
        env["CLIMATE_TIMER_OFF"],
        env["CLIMATE_SWING_VERTICAL_LEVEL"],
        env["CLIMATE_SWING_HORIZONTAL_LEVEL"],
        env["CLIMATE_ENERGY"],
        env["CLIMATE_TEMPERATURE_OUTDOOR"],
    ):
        assert required_key in climate_commands


def test_cloud_get_commands_uses_declared_policy_without_shrinking_climate() -> None:
    env = _runtime_env()
    get_commands = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="_get_commands",
        globals_env=env,
    )

    washer_declared = [
        env["WASHING_MACHINE_CURRENT_PROGRESS"],
        env["WASHING_MACHINE_OPERATING_STATUS"],
        env["WASHING_MACHINE_CURRENT_MODE"],
    ]
    climate_declared = [
        env["CLIMATE_POWER"],
        env["CLIMATE_OPERATING_MODE"],
        env["CLIMATE_TARGET_TEMPERATURE"],
    ]

    class Client:
        _commands = [{"has": "remote metadata"}]
        _commands_info = {
            "DSH": [
                {
                    "DeviceType": str(env["DEVICE_TYPE_WASHING_MACHINE"]),
                    "CommandTypes": washer_declared,
                }
            ],
            "PXGD": [
                {
                    "DeviceType": str(env["DEVICE_TYPE_CLIMATE"]),
                    "CommandTypes": climate_declared,
                }
            ],
        }

    washer_payload = get_commands(
        Client(), env["DEVICE_TYPE_WASHING_MACHINE"], "DSH", "NA-V123"
    )
    climate_payload = get_commands(
        Client(), env["DEVICE_TYPE_CLIMATE"], "PXGD", "CS-PX36FA2"
    )

    assert _command_type_values(washer_payload) == washer_declared

    climate_commands = _command_type_values(climate_payload)
    assert climate_commands != climate_declared
    assert env["CLIMATE_TEMPERATURE_INDOOR"] in climate_commands
    assert env["CLIMATE_AIRFRESH_MODE"] in climate_commands
    assert env["CLIMATE_SWING_VERTICAL_LEVEL"] in climate_commands


def test_dsh_washer_has_model_specific_current_progress_sensor() -> None:
    _source_contains(
        WASHER_DESCRIPTIONS_PATH,
        "WASHING_MACHINE_DSH_SENSORS",
        "WASHING_MACHINE_SENSORS_BY_MODEL",
        "WASHING_MACHINE_CURRENT_PROGRESS",
        "工程訊息",
    )
    _source_contains(
        SENSOR_PLATFORM_PATH,
        "WASHING_MACHINE_SENSORS_BY_MODEL",
        "info.get(\"ModelType\", \"\")",
    )


def test_rph_washer_exposes_dryer_status_sensors() -> None:
    env = _runtime_env()

    assert env["WASHING_MACHINE_DRYING_TIME"] == "0x49"
    assert env["WASHING_MACHINE_DRYING_METHOD"] == "0x4C"
    _source_contains(
        WASHER_DESCRIPTIONS_PATH,
        "WASHING_MACHINE_RPH_SENSORS",
        "WASHING_MACHINE_DRYING_TIME",
        "乾燥時間設定",
        "WASHING_MACHINE_DRYING_METHOD",
        "乾燥方法設定",
        '"RPH": WASHING_MACHINE_RPH_SENSORS',
    )


def test_cn_stack_exposes_program_status_sensors() -> None:
    env = _runtime_env()

    assert env["WASHING_MACHINE_PROGRAM_1"] == "0x34"
    assert env["DRYER_PROGRAM_1"] == "0x34"
    assert env["DRYER_PROGRAM_2"] == "0x64"
    _source_contains(
        WASHER_DESCRIPTIONS_PATH,
        "WASHING_MACHINE_CN_RW_SENSORS",
        "WASHING_MACHINE_PROGRAM_1",
        "工程資訊",
        '"CN-RW": WASHING_MACHINE_CN_RW_SENSORS',
    )
    _source_contains(
        DRYER_DESCRIPTIONS_PATH,
        "DRYER_PROGRAM_1",
        "DRYER_PROGRAM_2",
        "工程資訊",
    )
