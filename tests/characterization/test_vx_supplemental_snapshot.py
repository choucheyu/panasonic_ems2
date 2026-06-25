"""Characterization tests for VX supplemental DeviceGetInfo snapshots."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import load_constant_assignments, load_method_function

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "device_get_info_vx_supplemental.json"


class _FakeApis:
    @staticmethod
    def post_device_get_info() -> str:
        return "DeviceGetInfo"


class _FakeClient:
    def __init__(self, response: dict[str, Any], workaround) -> None:
        self._cp_token = "TOKEN_REDACTED"
        self.response = response
        self.requests: list[dict[str, Any]] = []
        self._workaround_info = lambda model_type, command_type, status: workaround(
            None,
            model_type,
            command_type,
            status,
        )

    async def request(self, **kwargs: Any) -> dict[str, Any]:
        self.requests.append(kwargs)
        return deepcopy(self.response)


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_cloud_method(method_name: str):
    constants = load_constant_assignments(CONST_PATH)
    constants["apis"] = _FakeApis
    constants["api_status"] = lambda func: func
    return constants, load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name=method_name,
        globals_env=constants,
    )


def test_vx_supplemental_snapshot_reads_only_requested_keys_and_normalizes_pm25() -> None:
    fixture = _load_fixture()
    constants, fetch_snapshot = _load_cloud_method("_fetch_device_command_snapshot")
    _, workaround = _load_cloud_method("_workaround_info")
    client = _FakeClient(fixture["response"], workaround)
    keys = [
        constants["CLIMATE_PM25"],
        constants["CLIMATE_MONITOR_MILDEW"],
        constants["CLIMATE_IMMEDIATE_MILDEW_DRY"],
        constants["CLIMATE_HUMIDITY_INDOOR"],
        constants["CLIMATE_VOICE"],
    ]

    snapshot = asyncio.run(fetch_snapshot(client, fixture["device"], 1, keys))

    assert snapshot == fixture["expected_snapshot"]
    assert constants["CLIMATE_PM25"] in snapshot
    assert snapshot[constants["CLIMATE_PM25"]] == 0
    assert "0x99" not in snapshot
    assert len(client.requests) == 1
    request = client.requests[0]
    assert request["method"] == "POST"
    assert request["endpoint"] == "DeviceGetInfo"
    assert request["headers"] == {
        "CPToken": "TOKEN_REDACTED",
        "auth": "AUTH_REDACTED",
        "GWID": "GWID_VX_1",
    }
    assert request["data"] == [
        {
            "DeviceID": 1,
            "CommandTypes": [{"CommandType": key} for key in keys],
        }
    ]


def test_vx_supplemental_snapshot_ignores_other_device_ids() -> None:
    fixture = _load_fixture()
    constants, fetch_snapshot = _load_cloud_method("_fetch_device_command_snapshot")
    _, workaround = _load_cloud_method("_workaround_info")
    client = _FakeClient(fixture["response"], workaround)
    keys = [constants["CLIMATE_HUMIDITY_INDOOR"]]

    snapshot = asyncio.run(fetch_snapshot(client, fixture["device"], 1, keys))

    assert snapshot == {constants["CLIMATE_HUMIDITY_INDOOR"]: 55}
    assert snapshot != {constants["CLIMATE_HUMIDITY_INDOOR"]: 45}


def test_merge_supplemental_status_adds_extras_without_removing_normal_status() -> None:
    fixture = _load_fixture()
    _, merge_status = _load_cloud_method("_merge_supplemental_status")
    info_list = deepcopy(fixture["existing_information"])

    merged = merge_status(None, info_list, {1: fixture["expected_snapshot"]})

    assert merged is info_list
    status = merged[0]["status"]
    assert status["0x00"] == 0
    assert status["0x01"] == 1
    assert status["0x02"] == 0
    assert status["0x37"] == 0
    assert status["0x53"] == 1
    assert status["0x55"] == 0
    assert status["0x57"] == 55
    assert status["0x59"] == 1


def test_merge_supplemental_status_leaves_unmatched_devices_untouched() -> None:
    fixture = _load_fixture()
    _, merge_status = _load_cloud_method("_merge_supplemental_status")
    info_list = deepcopy(fixture["existing_information"])

    merged = merge_status(None, info_list, {2: {"0x57": 45}})

    assert merged == fixture["existing_information"]


def test_vx_model_type_uses_expected_supplemental_key_set() -> None:
    constants, get_keys = _load_cloud_method("_get_supplemental_keys")
    fixture = _load_fixture()

    keys = get_keys(None, fixture["device"])

    assert keys == constants["SUPPLEMENTAL_COMMANDS"][str(constants["DEVICE_TYPE_CLIMATE"])]["VX"]
    assert set(keys) == set(fixture["expected_snapshot"])
