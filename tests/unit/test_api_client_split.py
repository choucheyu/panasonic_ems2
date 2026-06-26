"""Phase 3 guards for splitting Panasonic API client modules out of cloud.py."""

from __future__ import annotations

import ast
import asyncio
import importlib.util
import logging
import sys
import types
from http import HTTPStatus
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "custom_components" / "panasonic_ems2"
API_PACKAGE = PACKAGE / "api"
CLOUD = PACKAGE / "core" / "cloud.py"
CORE_APIS = PACKAGE / "core" / "apis.py"
CORE_EXCEPTIONS = PACKAGE / "core" / "exceptions.py"


def _load_api_module(module_name: str):
    """Load api/<module>.py without importing the HA-dependent integration package root."""
    package_name = "phase3_panasonic_api"
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(API_PACKAGE)]
        sys.modules[package_name] = package

    full_name = f"{package_name}.{module_name}"
    if full_name in sys.modules:
        del sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, API_PACKAGE / f"{module_name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, status: int, payload: Any = None, *, json_error: Exception | None = None) -> None:
        self.status = status
        self.payload = payload
        self.json_error = json_error
        self.text = "plain text payload"

    async def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class _Session:
    def __init__(self, response: _Response | None = None, *, raises: Exception | None = None) -> None:
        self.response = response or _Response(HTTPStatus.OK, {"ok": True})
        self.raises = raises
        self.calls: list[dict[str, Any]] = []

    async def request(self, method, *, url, json=None, params=None, headers=None, timeout=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "json": json,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.raises is not None:
            raise self.raises
        return self.response


def _cloud_method_node(method_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse(CLOUD.read_text(encoding="utf-8"), filename=str(CLOUD))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PanasonicSmartHome":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"PanasonicSmartHome.{method_name} not found")


def test_api_package_has_client_endpoints_errors_and_token_store_modules() -> None:
    assert (API_PACKAGE / "__init__.py").exists()
    assert (API_PACKAGE / "client.py").exists()
    assert (API_PACKAGE / "endpoints.py").exists()
    assert (API_PACKAGE / "errors.py").exists()
    assert (API_PACKAGE / "token_store.py").exists()


def test_endpoint_module_preserves_existing_core_api_urls() -> None:
    endpoints = _load_api_module("endpoints")

    assert endpoints.BASE_URL == "https://ems2.panasonic.com.tw/api"
    assert endpoints.open_session() == "https://ems2.panasonic.com.tw/api/userlogin1"
    assert endpoints.close_session() == "https://ems2.panasonic.com.tw/api/userlogout1"
    assert endpoints.refresh_token() == "https://ems2.panasonic.com.tw/api/RefreshToken1"
    assert endpoints.get_user_info() == "https://ems2.panasonic.com.tw/api/UserGetInfo"
    assert endpoints.get_update_info() == "https://ems2.panasonic.com.tw/PSHE_MI/api/S3/UpdateCheck"
    assert endpoints.get_user_devices() == "https://ems2.panasonic.com.tw/api/UserGetRegisteredGwList2"
    assert endpoints.get_gw_ip() == "https://ems2.panasonic.com.tw/api/UserGetGWIP"
    assert endpoints.post_device_get_info() == "https://ems2.panasonic.com.tw/api/DeviceGetInfo"
    assert endpoints.get_device_status() == "https://ems2.panasonic.com.tw/api/UserGetDeviceStatus"
    assert endpoints.get_plate_mode() == "https://ems2.panasonic.com.tw/api/PlateGetMode"
    assert endpoints.set_device() == "https://ems2.panasonic.com.tw/api/DeviceSetCommand"


def test_error_module_is_the_single_export_source_for_core_exceptions() -> None:
    errors = _load_api_module("errors")
    core_exceptions_source = CORE_EXCEPTIONS.read_text(encoding="utf-8")
    assert "from ..api.errors import" in core_exceptions_source

    for name in [
        "Ems2BaseException",
        "Ems2TokenNotFound",
        "Ems2TokenExpired",
        "Ems2InvalidRefreshToken",
        "Ems2TooManyRequest",
        "Ems2LoginFailed",
        "Ems2Expectation",
        "Ems2ExceedRateLimit",
    ]:
        assert name in core_exceptions_source
        assert hasattr(errors, name)


def test_api_client_request_adds_headers_counts_and_returns_json_dict() -> None:
    PanasonicApiClient = _load_api_module("client").PanasonicApiClient

    headers = {"CPToken": "token"}
    session = _Session(_Response(HTTPStatus.OK, {"status": "success"}))
    client = PanasonicApiClient(
        session=session,
        account="user@example.com",
        user_agent="test-agent",
        request_timeout=12,
    )

    result = asyncio.run(
        client.request(
            "POST",
            headers=headers,
            endpoint="https://example.invalid/api",
            params={"p": "1"},
            data={"hello": "world"},
        )
    )

    assert result == {"status": "success"}
    assert client.api_counts == 1
    assert client.api_counts_per_hour == 1
    assert session.calls == [
        {
            "method": "POST",
            "url": "https://example.invalid/api",
            "json": {"hello": "world"},
            "params": {"p": "1"},
            "headers": {
                "CPToken": "token",
                "user-agent": "test-agent",
                "Content-Type": "application/json",
            },
            "timeout": 12,
        }
    ]


@pytest.mark.parametrize(
    ("status", "exception_name"),
    [
        (HTTPStatus.BAD_REQUEST, "Ems2ExceedRateLimit"),
        (HTTPStatus.FORBIDDEN, "Ems2LoginFailed"),
        (HTTPStatus.TOO_MANY_REQUESTS, "Ems2TooManyRequest"),
        (HTTPStatus.EXPECTATION_FAILED, "Ems2Expectation"),
        (HTTPStatus.INTERNAL_SERVER_ERROR, "Ems2TokenNotFound"),
    ],
)
def test_api_client_request_preserves_status_exception_mapping(status, exception_name) -> None:
    errors = _load_api_module("errors")
    PanasonicApiClient = _load_api_module("client").PanasonicApiClient

    session = _Session(_Response(status, {}))
    client = PanasonicApiClient(session=session, account="user@example.com")

    with pytest.raises(getattr(errors, exception_name)):
        asyncio.run(client.request("GET", headers={}, endpoint="https://example.invalid/api"))


@pytest.mark.parametrize("payload", ["text", [1, 2, 3]])
def test_api_client_request_wraps_non_dict_success_payloads(payload) -> None:
    PanasonicApiClient = _load_api_module("client").PanasonicApiClient

    session = _Session(_Response(HTTPStatus.OK, payload))
    client = PanasonicApiClient(session=session, account="user@example.com")

    assert asyncio.run(client.request("GET", headers={}, endpoint="https://example.invalid/api")) == {"data": payload}


def test_api_client_request_returns_empty_dict_on_transport_error() -> None:
    PanasonicApiClient = _load_api_module("client").PanasonicApiClient

    session = _Session(raises=TimeoutError("timeout"))
    client = PanasonicApiClient(session=session, account="user@example.com")

    assert asyncio.run(client.request("GET", headers={}, endpoint="https://example.invalid/api")) == {}
    assert client.api_counts == 1
    assert client.api_counts_per_hour == 1


def test_api_client_transport_error_log_redacts_account_and_exception_detail(caplog) -> None:
    PanasonicApiClient = _load_api_module("client").PanasonicApiClient

    account = "sensitive.user@example.com"
    session = _Session(raises=TimeoutError(f"timeout while fetching {account}"))
    client = PanasonicApiClient(session=session, account=account)
    caplog.set_level(logging.WARNING)

    assert asyncio.run(client.request("GET", headers={}, endpoint="https://example.invalid/api")) == {}

    assert account not in caplog.text
    assert "sensitive.user" not in caplog.text
    assert "timeout while fetching" not in caplog.text
    assert "account=<redacted>" in caplog.text


def test_cloud_uses_api_client_and_token_store_seams_instead_of_owning_http_logic() -> None:
    cloud_source = CLOUD.read_text(encoding="utf-8")
    assert "from ..api.client import PanasonicApiClient" in cloud_source
    assert "from ..api.token_store import PanasonicTokenStore" in cloud_source
    assert "from ..api import endpoints as apis" in cloud_source
    assert "from ..api.errors import" in cloud_source

    request_method = _cloud_method_node("request")
    request_source = ast.get_source_segment(cloud_source, request_method)
    assert request_source is not None
    assert "self._api_client.request" in request_source
    assert "self._session.request" not in request_source
    assert "HTTPStatus" not in request_source

    init_method = _cloud_method_node("__init__")
    init_source = ast.get_source_segment(cloud_source, init_method)
    assert init_source is not None
    assert "PanasonicApiClient(" in init_source
    assert "PanasonicTokenStore(" in init_source


def test_token_store_module_defines_load_save_account_count_and_stop_listener_seams() -> None:
    token_store_path = API_PACKAGE / "token_store.py"
    tree = ast.parse(token_store_path.read_text(encoding="utf-8"), filename=str(token_store_path))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    assert "PanasonicTokenStore" in classes

    method_names = {
        child.name
        for child in classes["PanasonicTokenStore"].body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert {
        "load_tokens",
        "store_tokens",
        "active_account_count",
        "async_listen_save_on_stop",
    } <= method_names

    core_apis_source = CORE_APIS.read_text(encoding="utf-8")
    core_exceptions_source = CORE_EXCEPTIONS.read_text(encoding="utf-8")
    assert "from ..api.endpoints import" in core_apis_source
    assert "from ..api.errors import" in core_exceptions_source
