"""Panasonic Smart Home support-bundle helper.

The script is intentionally standalone so users can run it outside Home Assistant
when they need help adding or fixing Panasonic Smart IoT TW device support.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from getpass import getpass
from http import HTTPStatus
from pathlib import Path
from typing import Any, Final, Literal
from urllib.parse import urlparse

import requests


HA_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
BASE_URL = "https://ems2.panasonic.com.tw/api"
APP_TOKEN = "D8CBFF4C-2824-4342-B22D-189166FEF503"

CONTENT_TYPE_JSON: Final = "application/json"
REQUEST_TIMEOUT = 15
SCRIPT_VERSION = "0.2.0"
DEFAULT_DEVICE_GET_INFO_BATCH_SIZE = 30
DEFAULT_SUPPLEMENTAL_BATCH_SIZE = 16
DEFAULT_REQUEST_DELAY_SECONDS = 0.1

OBSERVATION_TEMPLATE = """## 裝置支援觀察補充

請在分享 support bundle 時，盡量補充以下資訊。這些人類觀察可以幫助判斷 CommandType 的真實語意，避免只靠 cloud metadata 暴露錯誤控制。

### 基本資訊
- 裝置型號：
- 官方 App 顯示的裝置名稱 / 類別：
- support bundle 檔名與收集時間：

### 當下狀態
- 官方 App 畫面顯示：
- 實體裝置狀態：
- Home Assistant 目前看到的實體 / 狀態：

### 若要確認控制行為，請填 before / after
- 操作前官方 App 狀態：
- 操作前實體裝置狀態：
- 做了什麼操作：
- 操作後官方 App 狀態：
- 操作後實體裝置狀態：
- 是否已恢復原狀：

### 注意
- 洗衣機等實體裝置請勿測試危險或不可逆操作。
- `開始洗衣` 這類動作只有在你明確願意測試時才提供 before/after。
"""

_LOGGER = logging.getLogger(__name__)


class Ems2BaseException(Exception):
    """Base exception."""


class Ems2TokenNotFound(Ems2BaseException):
    """Refresh token not found."""


class Ems2TokenExpired(Ems2BaseException):
    """Token expired."""


class Ems2InvalidRefreshToken(Ems2BaseException):
    """Refresh token expired."""


class Ems2TooManyRequest(Ems2BaseException):
    """Too many requests."""


class Ems2LoginFailed(Ems2BaseException):
    """Login failed."""


class Ems2Expectation(Ems2BaseException):
    """Expectation failed."""


class Ems2ExceedRateLimit(Ems2BaseException):
    """API reaches rate limit."""


class apis:  # noqa: N801 - keep historical script API shape
    """Panasonic EMS2 endpoint builders."""

    @staticmethod
    def open_session():
        return f"{BASE_URL}/userlogin1"

    @staticmethod
    def get_user_devices():
        return f"{BASE_URL}/UserGetRegisteredGwList2"

    @staticmethod
    def get_device_status():
        return f"{BASE_URL}/UserGetDeviceStatus"

    @staticmethod
    def post_device_get_info():
        return f"{BASE_URL}/DeviceGetInfo"

    @staticmethod
    def get_user_info():
        return f"{BASE_URL}/UserGetInfo"

    @staticmethod
    def get_update_info():
        return "https://ems2.panasonic.com.tw/PSHE_MI/api/S3/UpdateCheck"


def _endpoint_label(endpoint: str) -> str:
    """Return a safe endpoint label without host query strings or secrets."""
    parsed = urlparse(endpoint)
    return parsed.path or endpoint


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_for_filename(collected_at: str) -> str:
    value = collected_at.replace("+00:00", "Z")
    return (
        value.replace(":", "")
        .replace("-", "")
        .replace("+", "")
        .replace("/", "")
    )


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    size = max(1, int(size))
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _coerce_json_payload(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _command_items(command_entry: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return CommandList item dictionaries from known Panasonic shapes."""
    raw = command_entry.get("JSON", command_entry.get("list", command_entry.get("List", [])))
    raw = _coerce_json_payload(raw)
    if isinstance(raw, Mapping):
        raw = raw.get("list", raw.get("List", []))
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, Mapping)]


def command_types_for_device(device: Mapping[str, Any], command_list: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return CommandList-backed command types for a device, preserving order."""
    model_type = str(device.get("ModelType", ""))
    device_type = str(device.get("DeviceType", ""))
    seen: set[str] = set()
    command_types: list[str] = []

    for command_entry in command_list:
        entry_model_type = str(command_entry.get("ModelType", ""))
        entry_device_type = str(command_entry.get("DeviceType", ""))
        if entry_model_type and entry_model_type != model_type:
            continue
        if entry_device_type and entry_device_type != device_type:
            continue
        for item in _command_items(command_entry):
            command_type = item.get("CommandType")
            if not isinstance(command_type, str) or not command_type:
                continue
            if command_type in seen:
                continue
            seen.add(command_type)
            command_types.append(command_type)
    return command_types


def _candidate_command_types(start: str = "0x00", end: str = "0x7F") -> list[str]:
    start_int = int(start, 16)
    end_int = int(end, 16)
    if end_int < start_int:
        start_int, end_int = end_int, start_int
    return [f"0x{value:02X}" for value in range(start_int, end_int + 1)]


class _Redactor:
    """Redact support-bundle data while preserving useful model metadata."""

    _SECRET_KEYS = {
        "account",
        "apptoken",
        "auth",
        "cptoken",
        "email",
        "memid",
        "password",
        "pw",
        "refreshtoken",
        "token",
    }
    _GWID_KEYS = {"gwid", "gw_id", "gatewayid"}
    _PERSONAL_NAME_KEYS = {"nickname", "devicename"}

    def __init__(self) -> None:
        self._gwid_map: dict[str, str] = {}
        self.redacted_fields: set[str] = set()

    def collect_gwids(self, value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if isinstance(key, str) and key.lower() in self._GWID_KEYS and isinstance(child, str):
                    self._gwid(child)
                elif isinstance(key, str) and key in self._gwid_map:
                    # Already-known GWID used as a dictionary key.
                    continue
                self.collect_gwids(child)
        elif isinstance(value, list):
            for child in value:
                self.collect_gwids(child)

    def _gwid(self, value: str) -> str:
        if value not in self._gwid_map:
            self._gwid_map[value] = f"GWID_{len(self._gwid_map) + 1}"
        self.redacted_fields.add("GWID")
        return self._gwid_map[value]

    def redact(self, value: Any, path: tuple[str, ...] = ()) -> Any:
        if isinstance(value, Mapping):
            redacted: dict[Any, Any] = {}
            for key, child in value.items():
                out_key = self._gwid(key) if isinstance(key, str) and key in self._gwid_map else key
                redacted[out_key] = self._redact_child(key, child, path)
            return redacted
        if isinstance(value, list):
            return [self.redact(child, path) for child in value]
        return value

    def _redact_child(self, key: Any, child: Any, path: tuple[str, ...]) -> Any:
        if not isinstance(key, str):
            return self.redact(child, path)
        lower_key = key.lower()
        child_path = (*path, key)

        if lower_key in self._GWID_KEYS and isinstance(child, str):
            return self._gwid(child)
        if lower_key in self._SECRET_KEYS or lower_key.endswith("token"):
            self.redacted_fields.add(key)
            return "[REDACTED]"
        if lower_key in self._PERSONAL_NAME_KEYS:
            self.redacted_fields.add(key)
            return "[REDACTED]"
        if key == "Name" and any(part in {"GwList", "Devices", "devices"} for part in path):
            self.redacted_fields.add("Name")
            return "[REDACTED]"
        return self.redact(child, child_path)


def _normalize_device_get_info_response(response: Mapping[str, Any], requested_keys: set[str]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    if response.get("status") != "success":
        return normalized
    for device_info in response.get("devices", []):
        if not isinstance(device_info, Mapping):
            continue
        device_id = str(device_info.get("DeviceID", "1"))
        status: dict[str, Any] = normalized.setdefault(device_id, {})
        for info in device_info.get("Info", []):
            if not isinstance(info, Mapping):
                continue
            command_type = info.get("CommandType")
            if command_type in requested_keys:
                status[str(command_type)] = info.get("status")
    return normalized


def build_support_bundle(
    info: Mapping[str, Any],
    *,
    collected_at: str | None = None,
    device_status: Mapping[str, Any] | None = None,
    device_get_info: Mapping[str, Any] | None = None,
    user_info: Mapping[str, Any] | None = None,
    update_check: Mapping[str, Any] | None = None,
    supplemental_probe: Mapping[str, Any] | None = None,
    redacted: bool = True,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build the shareable Panasonic support bundle."""
    raw_bundle: dict[str, Any] = {
        "script_version": SCRIPT_VERSION,
        "collected_at": collected_at or _utc_now_iso(),
        "devices": deepcopy(info.get("GwList", [])),
        "command_list": deepcopy(info.get("CommandList", [])),
        "device_status": deepcopy(device_status or {}),
        "device_get_info": deepcopy(device_get_info or {}),
        "user_info": deepcopy(user_info or {}),
        "update_check": deepcopy(update_check or {}),
        "supplemental_probe": deepcopy(
            supplemental_probe
            or {
                "enabled": False,
                "note": "Supplemental probe is opt-in because it increases read-only DeviceGetInfo calls.",
            }
        ),
        "observation_template": OBSERVATION_TEMPLATE,
        "errors": errors or [],
    }

    if not redacted:
        raw_bundle["redaction"] = {
            "enabled": False,
            "warning": "Raw output may contain identifiers, auth headers, nicknames, or other personal data.",
        }
        return raw_bundle

    redactor = _Redactor()
    redactor.collect_gwids(raw_bundle)
    bundle = redactor.redact(raw_bundle)
    bundle["redaction"] = {
        "enabled": True,
        "fields": sorted(redactor.redacted_fields),
        "note": "Auth/tokens/account-like values, GWIDs, nicknames, and device names are redacted by default.",
    }
    return bundle


def write_support_files(
    bundle: Mapping[str, Any],
    *,
    output_dir: str | Path = ".",
    legacy_files: bool = True,
    bundle_name: str | None = None,
) -> dict[str, Path]:
    """Write the support bundle and optional legacy compatibility files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    if bundle_name is None:
        timestamp = _timestamp_for_filename(str(bundle.get("collected_at", _utc_now_iso())))
        bundle_name = f"panasonic_ems2_support_bundle_{timestamp}.json"
    bundle_path = output_path / bundle_name
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    paths = {"bundle": bundle_path}
    if legacy_files:
        devices_path = output_path / "panasonic_devices.json"
        commands_path = output_path / "panasonic_commands.json"
        devices_path.write_text(json.dumps(bundle.get("devices", []), indent=2, ensure_ascii=False), encoding="utf-8")
        commands_path.write_text(json.dumps(bundle.get("command_list", []), indent=2, ensure_ascii=False), encoding="utf-8")
        paths["devices"] = devices_path
        paths["commands"] = commands_path
    return paths


class PanasonicSmartHome:
    """Panasonic Smart Home support collector."""

    def __init__(self, hass, session, account, password):
        self.hass = hass
        self.email = account
        self.password = password
        self._session = session
        self._devices: list[dict[str, Any]] = []
        self._commands: list[dict[str, Any]] = []
        self._cp_token = ""
        self._refresh_token = None
        self._expires_in = 0
        self._expire_time = None
        self._token_timeout = None
        self._refresh_token_timeout = None
        self._mversion = None
        self._update_timestamp = None
        self._api_counts = 0
        self._api_counts_per_hour = 0
        self.errors: list[str] = []

    async def request(
        self,
        method: Literal["GET", "POST"],
        headers,
        endpoint: str,
        params=None,
        data=None,
    ):
        """Shared request method."""
        res: Any = {}
        headers["user-agent"] = HA_USER_AGENT
        headers["Content-Type"] = CONTENT_TYPE_JSON

        self._api_counts += 1
        self._api_counts_per_hour += 1
        try:
            if self._session:
                response = await self._session.request(
                    method,
                    url=endpoint,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )
            else:
                response = requests.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )
        except requests.exceptions.RequestException as ex:
            message = f"request failed: {method} {_endpoint_label(endpoint)} ({ex.__class__.__name__})"
            _LOGGER.error(message)
            self.errors.append(message)
            return {}
        except Exception as ex:  # pragma: no cover - defensive for aiohttp/session variants
            message = f"request exception: {method} {_endpoint_label(endpoint)} ({ex.__class__.__name__})"
            _LOGGER.error(message)
            self.errors.append(message)
            return {}

        if self._session:
            if response.status == HTTPStatus.OK:
                try:
                    res = await response.json()
                except Exception as ex:  # pragma: no cover - defensive
                    message = f"json parse failed: {method} {_endpoint_label(endpoint)} ({ex.__class__.__name__})"
                    _LOGGER.error(message)
                    self.errors.append(message)
                    res = {}
            elif response.status == HTTPStatus.BAD_REQUEST:
                raise Ems2ExceedRateLimit
            elif response.status == HTTPStatus.FORBIDDEN:
                raise Ems2LoginFailed
            elif response.status == HTTPStatus.TOO_MANY_REQUESTS:
                raise Ems2TooManyRequest
            elif response.status == HTTPStatus.EXPECTATION_FAILED:
                raise Ems2Expectation
            elif response.status == HTTPStatus.NOT_FOUND:
                _LOGGER.warning("Use wrong method or parameters: %s %s", method, _endpoint_label(endpoint))
                res = {}
            else:
                raise Ems2TokenNotFound
        else:
            if response.status_code == HTTPStatus.OK:
                try:
                    res = response.json()
                except ValueError as ex:
                    message = f"json parse failed: {method} {_endpoint_label(endpoint)} ({ex.__class__.__name__})"
                    _LOGGER.error(message)
                    self.errors.append(message)
                    res = {}
            elif response.status_code == HTTPStatus.FORBIDDEN:
                print("Login failed, please check your email or password!")
            elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                print("Login too many times, please wait for one hour, then try again")
            elif response.status_code == HTTPStatus.EXPECTATION_FAILED:
                print("Exception, please wait for one hour, then try again")

        if isinstance(res, list):
            return {"data": res}
        return res

    async def login(self):
        """Login to get an access token."""
        data = {"MemId": self.email, "PW": self.password, "AppToken": APP_TOKEN}
        response = await self.request(
            method="POST", headers={}, endpoint=apis.open_session(), data=data
        )
        self._cp_token = response.get("CPToken", "") if isinstance(response, Mapping) else ""
        self._refresh_token = response.get("RefreshToken", "") if isinstance(response, Mapping) else ""
        self._token_timeout = response.get("TokenTimeOut", "") if isinstance(response, Mapping) else ""
        self._refresh_token_timeout = response.get("RefreshTokenTimeOut", "") if isinstance(response, Mapping) else ""
        self._mversion = response.get("MVersion", "") if isinstance(response, Mapping) else ""

    async def get_user_devices(self):
        """List devices and command metadata available to the user."""
        header = {"CPToken": self._cp_token}
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_user_devices()
        )

        if isinstance(response, Mapping):
            self._devices = list(response.get("GwList", []))
            self._commands = list(response.get("CommandList", []))
        return self._devices, self._commands

    async def get_device_status_snapshot(self) -> dict[str, Any]:
        """Collect read-only UserGetDeviceStatus snapshot."""
        header = {"CPToken": self._cp_token, "apptype": "Smart"}
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_device_status()
        )
        return dict(response) if isinstance(response, Mapping) else {}

    async def get_device_get_info_snapshots(
        self,
        devices: Sequence[Mapping[str, Any]],
        command_list: Sequence[Mapping[str, Any]],
        *,
        batch_size: int = DEFAULT_DEVICE_GET_INFO_BATCH_SIZE,
        request_delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Collect read-only DeviceGetInfo snapshots for CommandList-backed commands."""
        snapshots: dict[str, dict[str, dict[str, Any]]] = {}
        for device in devices:
            gwid = device.get("GWID")
            if not isinstance(gwid, str) or not gwid:
                continue
            command_types = command_types_for_device(device, command_list)
            if not command_types:
                continue
            device_ids = [
                dev.get("DeviceID", 1)
                for dev in device.get("Devices", [{"DeviceID": 1}])
                if isinstance(dev, Mapping)
            ] or [1]
            headers = {"CPToken": self._cp_token, "auth": device.get("Auth", ""), "GWID": gwid}
            for chunk in _chunks(command_types, batch_size):
                data = [
                    {
                        "DeviceID": device_id,
                        "CommandTypes": [{"CommandType": command_type} for command_type in chunk],
                    }
                    for device_id in device_ids
                ]
                response = await self.request(
                    method="POST",
                    headers=dict(headers),
                    data=data,
                    endpoint=apis.post_device_get_info(),
                )
                if isinstance(response, Mapping):
                    normalized = _normalize_device_get_info_response(response, set(chunk))
                    gwid_snapshot = snapshots.setdefault(gwid, {})
                    for device_id, status in normalized.items():
                        gwid_snapshot.setdefault(device_id, {}).update(status)
                if request_delay > 0:
                    await asyncio.sleep(request_delay)
        return snapshots

    async def get_user_info_snapshots(self) -> dict[str, Any]:
        """Collect read-only UserGetInfo snapshots for statistics-capable data."""
        header = {"CPToken": self._cp_token}
        base_data = {
            "name": "",
            "from": datetime.today().replace(day=1).strftime("%Y/%m/%d"),
            "unit": "day",
            "max_num": 31,
        }
        snapshots: dict[str, Any] = {}
        for info_type in ("Power", "Other"):
            data = dict(base_data)
            data["name"] = info_type
            response = await self.request(
                method="POST", headers=dict(header), data=data, endpoint=apis.get_user_info()
            )
            snapshots[info_type] = dict(response) if isinstance(response, Mapping) else {}
        return snapshots

    async def get_update_check_snapshot(self) -> dict[str, Any]:
        """Collect read-only firmware/update-check snapshot."""
        header = {"CPToken": self._cp_token, "apptype": "Smart"}
        response = await self.request(
            method="GET", headers=header, endpoint=apis.get_update_info()
        )
        return dict(response) if isinstance(response, Mapping) else {}

    async def get_supplemental_probe_snapshots(
        self,
        devices: Sequence[Mapping[str, Any]],
        command_list: Sequence[Mapping[str, Any]],
        *,
        start: str = "0x00",
        end: str = "0x7F",
        batch_size: int = DEFAULT_SUPPLEMENTAL_BATCH_SIZE,
        request_delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
    ) -> dict[str, Any]:
        """Optionally probe non-CommandList DeviceGetInfo keys in small read-only batches."""
        result: dict[str, Any] = {
            "enabled": True,
            "range": {"start": start, "end": end},
            "snapshots": {},
        }
        all_candidates = _candidate_command_types(start, end)
        snapshots: dict[str, dict[str, dict[str, Any]]] = {}
        for device in devices:
            gwid = device.get("GWID")
            if not isinstance(gwid, str) or not gwid:
                continue
            commandlist_keys = set(command_types_for_device(device, command_list))
            candidates = [key for key in all_candidates if key not in commandlist_keys]
            if not candidates:
                continue
            device_ids = [
                dev.get("DeviceID", 1)
                for dev in device.get("Devices", [{"DeviceID": 1}])
                if isinstance(dev, Mapping)
            ] or [1]
            headers = {"CPToken": self._cp_token, "auth": device.get("Auth", ""), "GWID": gwid}
            for chunk in _chunks(candidates, batch_size):
                data = [
                    {
                        "DeviceID": device_id,
                        "CommandTypes": [{"CommandType": command_type} for command_type in chunk],
                    }
                    for device_id in device_ids
                ]
                response = await self.request(
                    method="POST",
                    headers=dict(headers),
                    data=data,
                    endpoint=apis.post_device_get_info(),
                )
                if isinstance(response, Mapping):
                    normalized = _normalize_device_get_info_response(response, set(chunk))
                    gwid_snapshot = snapshots.setdefault(gwid, {})
                    for device_id, status in normalized.items():
                        gwid_snapshot.setdefault(device_id, {}).update(status)
                if request_delay > 0:
                    await asyncio.sleep(request_delay)
        result["snapshots"] = snapshots
        return result

    async def get_devices_info(self):
        """Backward-compatible method returning GwList and CommandList."""
        await self.login()
        info = {"GwList": [], "CommandList": []}
        if self._cp_token:
            devices, commands = await self.get_user_devices()
            info["GwList"] = devices
            info["CommandList"] = commands
        else:
            print("Have problem to login, please check your account and password!")
        return info

    async def collect_support_bundle(
        self,
        *,
        redacted: bool = True,
        include_device_status: bool = True,
        include_device_get_info: bool = True,
        include_user_info: bool = True,
        include_update_check: bool = True,
        probe_supplemental: bool = False,
        supplemental_start: str = "0x00",
        supplemental_end: str = "0x7F",
        device_get_info_batch_size: int = DEFAULT_DEVICE_GET_INFO_BATCH_SIZE,
        supplemental_batch_size: int = DEFAULT_SUPPLEMENTAL_BATCH_SIZE,
        request_delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
    ) -> dict[str, Any]:
        """Collect a redacted support bundle for device-support analysis."""
        await self.login()
        info = {"GwList": [], "CommandList": []}
        device_status: Mapping[str, Any] = {}
        device_get_info: Mapping[str, Any] = {}
        user_info: Mapping[str, Any] = {}
        update_check: Mapping[str, Any] = {}
        supplemental_probe: Mapping[str, Any] | None = None

        if not self._cp_token:
            print("Have problem to login, please check your account and password!")
            return build_support_bundle(info, redacted=redacted, errors=self.errors)

        devices, commands = await self.get_user_devices()
        info = {"GwList": devices, "CommandList": commands}

        if include_device_status:
            device_status = await self.get_device_status_snapshot()
        if include_device_get_info:
            device_get_info = await self.get_device_get_info_snapshots(
                devices,
                commands,
                batch_size=device_get_info_batch_size,
                request_delay=request_delay,
            )
        if include_user_info:
            user_info = await self.get_user_info_snapshots()
        if include_update_check:
            update_check = await self.get_update_check_snapshot()
        if probe_supplemental:
            supplemental_probe = await self.get_supplemental_probe_snapshots(
                devices,
                commands,
                start=supplemental_start,
                end=supplemental_end,
                batch_size=supplemental_batch_size,
                request_delay=request_delay,
            )

        return build_support_bundle(
            info,
            device_status=device_status,
            device_get_info=device_get_info,
            user_info=user_info,
            update_check=update_check,
            supplemental_probe=supplemental_probe,
            redacted=redacted,
            errors=self.errors,
        )


async def get_devices(
    username,
    password,
    *,
    output_dir: str | Path = ".",
    raw_output: bool = False,
    legacy_files: bool = True,
    include_device_status: bool = True,
    include_device_get_info: bool = True,
    include_user_info: bool = True,
    include_update_check: bool = True,
    probe_supplemental: bool = False,
    supplemental_start: str = "0x00",
    supplemental_end: str = "0x7F",
    request_delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
):
    """Collect support data and write bundle files."""
    client = PanasonicSmartHome(None, None, username, password)
    bundle = await client.collect_support_bundle(
        redacted=not raw_output,
        include_device_status=include_device_status,
        include_device_get_info=include_device_get_info,
        include_user_info=include_user_info,
        include_update_check=include_update_check,
        probe_supplemental=probe_supplemental,
        supplemental_start=supplemental_start,
        supplemental_end=supplemental_end,
        request_delay=request_delay,
    )
    paths = write_support_files(bundle, output_dir=output_dir, legacy_files=legacy_files)
    if bundle.get("devices"):
        print("\nGenerated Panasonic EMS2 support files:")
        for label, path in paths.items():
            print(f"- {label}: {path}")
        if bundle.get("redaction", {}).get("enabled"):
            print("\nThe support bundle is redacted by default. Review it before sharing.")
        else:
            print("\nWARNING: raw output may contain identifiers or auth-like values. Review it before sharing.")
    return bundle


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect a redacted Panasonic EMS2 support bundle for device-support issues."
    )
    parser.add_argument("--output-dir", default=".", help="Directory for generated JSON files.")
    parser.add_argument(
        "--raw-output",
        action="store_true",
        help="Disable default redaction. Use only for private/local debugging.",
    )
    parser.add_argument(
        "--no-legacy-files",
        action="store_true",
        help="Only write the support bundle; skip legacy panasonic_devices.json/panasonic_commands.json.",
    )
    parser.add_argument("--skip-status", action="store_true", help="Skip UserGetDeviceStatus snapshot.")
    parser.add_argument("--skip-device-get-info", action="store_true", help="Skip DeviceGetInfo snapshots.")
    parser.add_argument("--skip-user-info", action="store_true", help="Skip UserGetInfo snapshots.")
    parser.add_argument("--skip-update-check", action="store_true", help="Skip S3/UpdateCheck snapshot.")
    parser.add_argument(
        "--probe-supplemental",
        action="store_true",
        help="Opt-in read-only probe for non-CommandList DeviceGetInfo keys. This increases API calls.",
    )
    parser.add_argument("--supplemental-start", default="0x00", help="Supplemental probe start key, e.g. 0x00.")
    parser.add_argument("--supplemental-end", default="0x7F", help="Supplemental probe end key, e.g. 0x7F.")
    parser.add_argument(
        "--request-delay",
        type=float,
        default=DEFAULT_REQUEST_DELAY_SECONDS,
        help="Delay between DeviceGetInfo batches in seconds.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # noqa: MC0001
    args = parse_args(argv)
    print(f"Version: {SCRIPT_VERSION}\n")
    username = input("Account: ")
    password = getpass()
    asyncio.run(
        get_devices(
            username,
            password,
            output_dir=args.output_dir,
            raw_output=args.raw_output,
            legacy_files=not args.no_legacy_files,
            include_device_status=not args.skip_status,
            include_device_get_info=not args.skip_device_get_info,
            include_user_info=not args.skip_user_info,
            include_update_check=not args.skip_update_check,
            probe_supplemental=args.probe_supplemental,
            supplemental_start=args.supplemental_start,
            supplemental_end=args.supplemental_end,
            request_delay=args.request_delay,
        )
    )


if __name__ == "__main__":
    main()
