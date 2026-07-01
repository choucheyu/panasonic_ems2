"""Regression guards for scoped Panasonic CommandList polling.

Cloud-declared CommandList metadata is useful for washer/dryer model support, but
it must not shrink climate polling. Panasonic climate CommandList is not a full
entity/status declaration, and treating it as one breaks existing PXGD/VX climate
sensors, selects, switches, and numbers.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tests.helpers.source_parsing import (
    _load_core_module,
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


def test_empty_global_commandlist_keeps_uxfa_climate_local_polling() -> None:
    env = _runtime_env()
    payload = env["build_polling_command_types"](
        env["DEVICE_TYPE_CLIMATE"],
        "UXFA",
        has_remote_commands=False,
        remote_command_types=None,
        capability_registry=env["CAPABILITY_REGISTRY"],
        model_jp_types=env["MODEL_JP_TYPES"],
    )

    commands = _command_type_values(payload)

    assert commands != [env["CLIMATE_POWER"]]
    assert env["CLIMATE_POWER"] in commands
    assert env["CLIMATE_OPERATING_MODE"] in commands
    assert env["CLIMATE_FAN_SPEED"] in commands
    assert env["CLIMATE_TARGET_TEMPERATURE"] in commands
    assert env["CLIMATE_TEMPERATURE_INDOOR"] in commands
    assert env["CLIMATE_SWING_VERTICAL_LEVEL"] in commands


def test_available_climate_with_empty_summary_status_is_polled() -> None:
    env = _runtime_env()
    cloud_commands = _load_core_module("cloud_commands")

    assert cloud_commands.should_poll_device_with_empty_summary_status(
        {
            "DeviceType": str(env["DEVICE_TYPE_CLIMATE"]),
            "ModelType": "UXFA",
            "Model": "CS-UX28FA2",
            "Devices": [{"DeviceID": 1, "IsAvailable": 1}],
        }
    ) is True
    assert cloud_commands.should_poll_device_with_empty_summary_status(
        {
            "DeviceType": str(env["DEVICE_TYPE_CLIMATE"]),
            "ModelType": "UXFA",
            "Devices": [{"DeviceID": 1, "IsAvailable": 0}],
        }
    ) is False
    assert cloud_commands.should_poll_device_with_empty_summary_status(
        {
            "DeviceType": str(env["DEVICE_TYPE_CLIMATE"]),
            "ModelType": "UXFA",
            "Devices": [{"DeviceID": 1, "IsAvailable": "false"}],
        }
    ) is False
    assert cloud_commands.should_poll_device_with_empty_summary_status(
        {
            "DeviceType": str(env["DEVICE_TYPE_WASHING_MACHINE"]),
            "ModelType": "HDH",
            "Devices": [{"DeviceID": 1, "IsAvailable": 1}],
        }
    ) is False


async def _no_delay_sleep(_delay: float) -> None:
    return None


def _get_devices_with_info_globals() -> dict[str, Any]:
    env = _runtime_env()
    cloud_commands = _load_core_module("cloud_commands")
    env.update(
        {
            "asyncio": SimpleNamespace(sleep=_no_delay_sleep),
            "apis": SimpleNamespace(get_device_status=lambda: "UserGetDeviceStatus"),
            "should_poll_device_with_empty_summary_status": (
                cloud_commands.should_poll_device_with_empty_summary_status
            ),
        }
    )
    return env


def _blank_status_response(gwid: str) -> dict[str, Any]:
    return {"GwList": [{"GWID": gwid, "List": [{"CommandType": "0x00", "Status": ""}]}]}


class _GetDevicesWithInfoClient:
    def __init__(
        self,
        *,
        device: dict[str, Any],
        response: dict[str, Any],
        existing_information: list[dict[str, Any]] | None = None,
    ) -> None:
        self._device = device
        self._response = response
        self._commands = []
        self._commands_info = {}
        self._cp_token = "-".join(("test", "token"))
        self._select_devices = []
        self._api_counts_per_hour = 100
        self._devices_info = {device["GWID"]: dict(device)}
        if existing_information is not None:
            self._devices_info[device["GWID"]]["Information"] = existing_information
        self.command_requests: list[tuple[Any, ...]] = []
        self.info_requests: list[str] = []
        self.supplemental_requests: list[str] = []

    async def get_user_devices(self) -> list[dict[str, Any]]:
        return [self._device]

    def _refactor_cmds_paras(self, _commands_info: dict[str, Any]) -> None:
        return None

    async def request(self, **_kwargs: Any) -> dict[str, Any]:
        return self._response

    def is_supported(self, _model_type: str) -> bool:
        return True

    def _get_commands(self, device_type: str, model_type: str, model: str) -> list[dict[str, str]]:
        self.command_requests.append((device_type, model_type, model))
        return [{"CommandType": "0x00"}]

    async def get_device_with_info(self, device: dict[str, Any], _func: list[dict[str, str]]) -> None:
        self.info_requests.append(device["GWID"])
        self._devices_info[device["GWID"]]["Information"] = [
            {"DeviceID": 1, "status": {"0x00": "1"}}
        ]

    def _get_supplemental_keys(self, device: dict[str, Any]) -> list[str]:
        self.supplemental_requests.append(device["GWID"])
        return []

    async def get_plate_info(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("weight-plate path should not run")

    async def get_user_info(self) -> bool:
        return True

    async def get_update_info(self, _check: bool = False) -> bool:
        return True


def test_get_devices_with_info_polls_available_uxfa_climate_with_blank_summary_status() -> None:
    env = _get_devices_with_info_globals()
    get_devices_with_info = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="get_devices_with_info",
        globals_env=env,
    )
    device = {
        "GWID": "GWID_CLIMATE",
        "DeviceType": str(env["DEVICE_TYPE_CLIMATE"]),
        "ModelType": "UXFA",
        "Model": "CS-UX28FA2",
        "Devices": [{"DeviceID": 1, "IsAvailable": 1}],
    }
    client = _GetDevicesWithInfoClient(
        device=device,
        response=_blank_status_response("GWID_CLIMATE"),
    )

    asyncio.run(get_devices_with_info(client))

    assert client.info_requests == ["GWID_CLIMATE"]
    assert client.command_requests == [
        (str(env["DEVICE_TYPE_CLIMATE"]), "UXFA", "CS-UX28FA2")
    ]
    assert client._devices_info["GWID_CLIMATE"]["Information"] == [
        {"DeviceID": 1, "status": {"0x00": "1"}}
    ]


def test_get_devices_with_info_preserves_washer_blank_summary_without_polling() -> None:
    env = _get_devices_with_info_globals()
    get_devices_with_info = load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="get_devices_with_info",
        globals_env=env,
    )
    existing_information = [{"DeviceID": 1, "status": {"0x50": "2"}}]
    device = {
        "GWID": "GWID_WASHER",
        "DeviceType": str(env["DEVICE_TYPE_WASHING_MACHINE"]),
        "ModelType": "HDH",
        "Model": "NA-V160HDH",
        "Devices": [{"DeviceID": 1, "IsAvailable": 1}],
    }
    client = _GetDevicesWithInfoClient(
        device=device,
        response=_blank_status_response("GWID_WASHER"),
        existing_information=existing_information,
    )

    asyncio.run(get_devices_with_info(client))

    assert client.info_requests == []
    assert client.command_requests == []
    assert client.supplemental_requests == []
    assert client._devices_info["GWID_WASHER"]["Information"] == existing_information


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


def test_lx128_uses_model_scoped_no_remote_fallback_without_start_or_warm_water() -> None:
    env = _runtime_env()
    expected_commands = [
        env["WASHING_MACHINE_CURRENT_PROGRESS"],
        env["WASHING_MACHINE_OPERATING_STATUS"],
        env["WASHING_MACHINE_CURRENT_MODE"],
        env["WASHING_MACHINE_LX128_REMAINING_WASH_TIME"],
        env["WASHING_MACHINE_NANOE_REMAINING_TIME"],
        env["WASHING_MACHINE_TIMER_REMAINING_TIME_OLD"],
        env["WASHING_MACHINE_ERROR_STATUS"],
        env["WASHING_MACHINE_TIMER"],
        env["WASHING_MACHINE_60"],
        env["WASHING_MACHINE_POSTPONE_DRYING_TIME"],
        env["WASHING_MACHINE_PROGRESS_NEW"],
    ]

    fallback = env["no_remote_command_types_for_model"](
        env["NO_REMOTE_COMMAND_TYPES"],
        env["DEVICE_TYPE_WASHING_MACHINE"],
        "LX128E",
    )
    empty_commandlist_payload = env["build_polling_command_types"](
        env["DEVICE_TYPE_WASHING_MACHINE"],
        "LX128E",
        has_remote_commands=True,
        remote_command_types=[],
        no_remote_command_types=fallback,
        capability_registry=env["CAPABILITY_REGISTRY"],
        model_jp_types=env["MODEL_JP_TYPES"],
    )
    missing_metadata_payload = env["build_polling_command_types"](
        env["DEVICE_TYPE_WASHING_MACHINE"],
        "LX128E",
        has_remote_commands=True,
        remote_command_types=None,
        no_remote_command_types=fallback,
        capability_registry=env["CAPABILITY_REGISTRY"],
        model_jp_types=env["MODEL_JP_TYPES"],
    )

    assert _command_type_values(empty_commandlist_payload) == expected_commands
    assert _command_type_values(missing_metadata_payload) == expected_commands
    assert env["WASHING_MACHINE_ENABLE"] not in expected_commands
    assert env["WASHING_MACHINE_WARM_WATER"] not in expected_commands
    _source_contains(
        WASHER_DESCRIPTIONS_PATH,
        "WASHING_MACHINE_LX128_SENSORS",
        "WASHING_MACHINE_LX128_REMAINING_WASH_TIME",
        "洗衣殘時間",
        "WASHING_MACHINE_NANOE_REMAINING_TIME",
        "nanoe殘時間",
        "WASHING_MACHINE_ERROR_STATUS",
        "異常狀態",
        '"LX128E": WASHING_MACHINE_LX128_SENSORS',
    )
