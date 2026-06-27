"""Guards for update-coordinator exception chaining."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

from tests.helpers.source_parsing import load_method_function

ROOT = Path(__file__).resolve().parents[2]
CLOUD = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"


def _cloud_method(method_name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    tree = ast.parse(CLOUD.read_text(encoding="utf-8"), filename=str(CLOUD))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PanasonicSmartHome":
            for child in node.body:
                if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)) and child.name == method_name:
                    return child
    raise AssertionError(f"PanasonicSmartHome.{method_name} not found")


def test_async_update_data_does_not_use_bare_except() -> None:
    method = _cloud_method("async_update_data")

    for node in ast.walk(method):
        if isinstance(node, ast.ExceptHandler):
            assert node.type is not None


def test_async_update_data_chains_update_failed_from_original_exception() -> None:
    method = _cloud_method("async_update_data")

    raises = [node for node in ast.walk(method) if isinstance(node, ast.Raise)]
    assert any(
        isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id == "UpdateFailed"
        and isinstance(node.cause, ast.Name)
        and node.cause.id == "err"
        for node in raises
    )


def test_api_status_logs_function_and_exception_class_without_raw_message() -> None:
    source = CLOUD.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CLOUD))
    api_status = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "api_status"
    )
    segment = ast.get_source_segment(source, api_status)
    assert segment is not None

    assert "Got exception" not in segment
    assert "func=%s exception=%s" in segment
    assert 'getattr(func, "__name__"' in segment
    assert "e.__class__.__name__" in segment
    assert "exc_info=True" in segment


def test_get_update_info_tolerates_short_update_info_rows() -> None:
    class FakeApis:
        @staticmethod
        def get_update_info() -> str:
            return "https://example.invalid/api/S3/UpdateCheck"

    get_update_info = load_method_function(
        CLOUD,
        class_name="PanasonicSmartHome",
        method_name="get_update_info",
        globals_env={
            "api_status": lambda func: func,
            "apis": FakeApis,
            "ENTITY_UPDATE": "update_available",
            "ENTITY_UPDATE_INFO": "update_version",
        },
    )

    class FakeClient:
        _cp_token = "token"
        _update_info = {}
        _devices_info = {
            "gw1": {"Information": [{"status": {}}]},
            "gw2": {"Information": [{"status": {}}]},
            "gw3": {"Information": []},
        }

        async def request(self, **kwargs):
            self.request_kwargs = kwargs
            return {
                "GwList": [
                    {"GwID": "gw1"},
                    {"GwID": "gw2"},
                    {"GwID": "gw3"},
                ],
                "UpdateInfo": [{"updateVersion": "1.2.3"}],
            }

    client = FakeClient()

    assert asyncio.run(get_update_info(client, check=True)) is True
    assert client._devices_info["gw1"]["Information"][0]["status"] == {
        "update_available": True,
        "update_version": "1.2.3",
    }
    assert client._devices_info["gw2"]["Information"][0]["status"] == {
        "update_available": True,
        "update_version": "",
    }
    assert client._devices_info["gw3"]["Information"] == []
