"""Guard tests for the standalone Panasonic support-bundle helper script."""

from __future__ import annotations

import asyncio
import builtins
import importlib.util
import json
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "panasonic_ems2.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("panasonic_support_script_under_test", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_imports_without_requests_dependency(monkeypatch) -> None:
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "requests":
            raise ModuleNotFoundError("No module named 'requests'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = _load_script_module()

    assert hasattr(module.requests, "request")
    assert issubclass(module.requests.exceptions.RequestException, Exception)


class _FakeResponse:
    status_code = HTTPStatus.OK

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


def test_sync_request_uses_json_parser_and_timeout(monkeypatch) -> None:
    module = _load_script_module()
    captured: dict[str, Any] = {}

    def fake_request(**kwargs):
        captured.update(kwargs)
        return _FakeResponse({"ok": True, "optional": None})

    monkeypatch.setattr(module.requests, "request", fake_request)
    client = module.PanasonicSmartHome(None, None, "user@example.com", "secret")

    result = asyncio.run(
        client.request(method="GET", headers={}, endpoint="https://example.test/api")
    )

    assert result == {"ok": True, "optional": None}
    assert captured["timeout"] == module.REQUEST_TIMEOUT


def test_support_bundle_redacts_sensitive_identifiers_but_preserves_command_metadata() -> None:
    module = _load_script_module()
    info = {
        "GwList": [
            {
                "GWID": "GWID_REAL_1",
                "Auth": "AUTH_REAL_1",
                "NickName": "住家洗衣機",
                "DeviceType": "3",
                "ModelType": "HDH",
                "Model": "NA-V160HDH",
                "Devices": [{"DeviceID": 1, "Name": "洗衣槽", "IsAvailable": True}],
            }
        ],
        "CommandList": [
            {
                "ModelType": "HDH",
                "DeviceType": 3,
                "GWID": "GWID_REAL_1",
                "Auth": "AUTH_REAL_1",
                "JSON": [
                    {
                        "CommandType": "0x50",
                        "CommandName": "運轉情報",
                        "ParameterType": "enum",
                        "Parameters": [["Standby", 1], ["Running", 2]],
                    }
                ],
            }
        ],
    }

    bundle = module.build_support_bundle(
        info,
        collected_at="2026-06-27T00:00:00+00:00",
        device_status={"GwList": [{"GWID": "GWID_REAL_1", "List": []}]},
        device_get_info={"GWID_REAL_1": {"1": {"0x50": 1}}},
        user_info={"Power": {"GwList": [{"GwID": "GWID_REAL_1", "Total_kwh": 1.2}]}},
        update_check={"GwList": [{"GwID": "GWID_REAL_1"}]},
        redacted=True,
    )

    dumped = json.dumps(bundle, ensure_ascii=False)
    assert "AUTH_REAL_1" not in dumped
    assert "GWID_REAL_1" not in dumped
    assert "住家洗衣機" not in dumped
    assert bundle["redaction"]["enabled"] is True
    assert bundle["devices"][0]["GWID"] == "GWID_1"
    assert bundle["command_list"][0]["JSON"][0]["CommandName"] == "運轉情報"
    assert bundle["device_get_info"]["GWID_1"]["1"] == {"0x50": 1}


def test_collect_support_bundle_fetches_read_only_snapshots(monkeypatch) -> None:
    module = _load_script_module()
    calls: list[dict[str, Any]] = []
    device = {
        "GWID": "GWID_REAL_1",
        "Auth": "AUTH_REAL_1",
        "NickName": "住家洗衣機",
        "DeviceType": "3",
        "ModelType": "HDH",
        "Model": "NA-V160HDH",
        "Devices": [{"DeviceID": 1, "Name": "洗衣槽", "IsAvailable": True}],
    }
    command_list = [
        {
            "ModelType": "HDH",
            "DeviceType": 3,
            "JSON": [
                {"CommandType": "0x50", "CommandName": "運轉情報"},
                {"CommandType": "0x64", "CommandName": "行程設定"},
            ],
        }
    ]

    async def fake_request(self, *, method, headers, endpoint, params=None, data=None):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "headers": dict(headers),
                "params": params,
                "data": data,
            }
        )
        if endpoint.endswith("/userlogin1"):
            return {"CPToken": "CP_TOKEN_REAL", "RefreshToken": "REFRESH_REAL"}
        if endpoint.endswith("/UserGetRegisteredGwList2"):
            return {"GwList": [device], "CommandList": command_list}
        if endpoint.endswith("/UserGetDeviceStatus"):
            return {"GwList": [{"GWID": "GWID_REAL_1", "List": [{"CommandType": "0x50", "Status": 1}]}]}
        if endpoint.endswith("/DeviceGetInfo"):
            return {
                "status": "success",
                "devices": [
                    {
                        "DeviceID": 1,
                        "Info": [
                            {"CommandType": "0x50", "status": 1},
                            {"CommandType": "0x64", "status": 3},
                        ],
                    }
                ],
            }
        if endpoint.endswith("/UserGetInfo"):
            return {"GwList": [{"GwID": "GWID_REAL_1", "Total_kwh": 1.2}]}
        if endpoint.endswith("/S3/UpdateCheck"):
            return {"GwList": [{"GwID": "GWID_REAL_1"}], "UpdateInfo": []}
        raise AssertionError(endpoint)

    monkeypatch.setattr(module.PanasonicSmartHome, "request", fake_request)
    client = module.PanasonicSmartHome(None, None, "user@example.com", "secret")

    bundle = asyncio.run(client.collect_support_bundle(redacted=True, include_user_info=True))

    endpoints = [call["endpoint"] for call in calls]
    assert any(endpoint.endswith("/UserGetDeviceStatus") for endpoint in endpoints)
    assert any(endpoint.endswith("/DeviceGetInfo") for endpoint in endpoints)
    assert any(endpoint.endswith("/UserGetInfo") for endpoint in endpoints)
    assert any(endpoint.endswith("/S3/UpdateCheck") for endpoint in endpoints)

    device_get_info_call = next(call for call in calls if call["endpoint"].endswith("/DeviceGetInfo"))
    assert device_get_info_call["method"] == "POST"
    assert device_get_info_call["headers"] == {
        "CPToken": "CP_TOKEN_REAL",
        "auth": "AUTH_REAL_1",
        "GWID": "GWID_REAL_1",
    }
    assert device_get_info_call["data"] == [
        {
            "DeviceID": 1,
            "CommandTypes": [{"CommandType": "0x50"}, {"CommandType": "0x64"}],
        }
    ]
    assert bundle["device_get_info"]["GWID_1"]["1"] == {"0x50": 1, "0x64": 3}


def test_write_support_files_creates_bundle_and_legacy_files(tmp_path) -> None:
    module = _load_script_module()
    bundle = {
        "script_version": "0.1.0",
        "collected_at": "2026-06-27T00:00:00+00:00",
        "devices": [{"GWID": "GWID_1", "ModelType": "HDH"}],
        "command_list": [{"ModelType": "HDH", "JSON": []}],
        "redaction": {"enabled": True},
    }

    paths = module.write_support_files(bundle, output_dir=tmp_path, legacy_files=True)

    assert paths["bundle"].name.startswith("panasonic_ems2_support_bundle_")
    assert json.loads(paths["bundle"].read_text(encoding="utf-8"))["script_version"] == "0.1.0"
    assert json.loads((tmp_path / "panasonic_devices.json").read_text(encoding="utf-8")) == bundle["devices"]
    assert json.loads((tmp_path / "panasonic_commands.json").read_text(encoding="utf-8")) == bundle["command_list"]
