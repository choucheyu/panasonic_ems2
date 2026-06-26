"""Phase 2 guards for shared described/range/writable entity helpers."""

from __future__ import annotations

import ast
import asyncio
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import load_method_function

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "custom_components" / "panasonic_ems2" / "core" / "base.py"
PLATFORM_FILES = (
    ROOT / "custom_components" / "panasonic_ems2" / "binary_sensor.py",
    ROOT / "custom_components" / "panasonic_ems2" / "sensor.py",
    ROOT / "custom_components" / "panasonic_ems2" / "select.py",
    ROOT / "custom_components" / "panasonic_ems2" / "number.py",
    ROOT / "custom_components" / "panasonic_ems2" / "switch.py",
)


@dataclass
class _Description:
    key: str
    name: str = "Fallback Name"
    options: list[str] = field(default_factory=list)
    options_value: list[str] = field(default_factory=list)


class _Client:
    def __init__(
        self,
        *,
        command_name: str | None = None,
        ranges: dict[str, dict[str, int]] | None = None,
    ) -> None:
        self.command_name = command_name
        self.ranges = ranges or {}
        self.set_calls: list[tuple[str, int, str, int]] = []
        self.update_calls: list[tuple[str, int]] = []

    def get_command_name(self, _gwid: str, _key: str) -> str | None:
        return self.command_name

    def get_range(self, _gwid: str, key: str) -> dict[str, int]:
        return self.ranges.get(key, {})

    async def set_device(self, gwid: str, device_id: int, key: str, value: int) -> None:
        self.set_calls.append((gwid, device_id, key, value))

    async def update_device(self, gwid: str, device_id: int) -> None:
        self.update_calls.append((gwid, device_id))


class _Entity:
    def __init__(
        self,
        *,
        description: _Description,
        client: _Client | None = None,
        info: dict[str, Any] | None = None,
    ) -> None:
        self.entity_description = description
        self.client = client or _Client()
        self.device_gwid = "GWID_SHARED"
        self.device_id = 1
        self.info = info or {
            "NickName": "測試裝置",
            "Devices": [{"DeviceID": 1, "Name": "子設備"}],
        }
        self.writes = 0

    def async_write_ha_state(self) -> None:
        self.writes += 1


def _load_top_level_function(path: Path, function_name: str, globals_env: dict[str, Any] | None = None):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            segment = ast.get_source_segment(source, node)
            if segment is None:
                raise AssertionError(f"source segment not found for {function_name}")
            namespace = dict(globals_env or {})
            exec(textwrap.dedent(segment), namespace)
            return namespace[function_name]
    raise AssertionError(f"{function_name} not found in {path}")


def _class_method(path: Path, class_name: str, method_name: str, globals_env: dict[str, Any] | None = None):
    return load_method_function(
        path,
        class_name=class_name,
        method_name=method_name,
        globals_env=globals_env or {},
    )


def _class_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def test_shared_get_key_from_dict_returns_matching_key_or_none() -> None:
    get_key_from_dict = _load_top_level_function(BASE, "get_key_from_dict")

    assert get_key_from_dict({"Auto": 0, "Cool": 1}, 1) == "Cool"
    assert get_key_from_dict({"Auto": 0, "Cool": 1}, 9) is None


def test_described_entity_common_name_and_unique_id_behavior() -> None:
    suffix = _class_method(BASE, "PanasonicDescribedEntity", "_entity_name_suffix")
    name = _class_method(BASE, "PanasonicDescribedEntity", "name")
    unique_id = _class_method(BASE, "PanasonicDescribedEntity", "unique_id")

    cloud_named = _Entity(
        description=_Description(key="0xAA", name="Fallback"),
        client=_Client(command_name="雲端名稱"),
    )
    fallback_named = _Entity(
        description=_Description(key="0xBB", name="本地名稱"),
        client=_Client(command_name=None),
    )
    cloud_named._entity_name_suffix = suffix.__get__(cloud_named, _Entity)
    fallback_named._entity_name_suffix = suffix.__get__(fallback_named, _Entity)

    assert name(cloud_named) == "測試裝置 雲端名稱"
    assert name(fallback_named) == "測試裝置 本地名稱"
    assert unique_id(cloud_named) == "GWID_SHARED_1_0xAA"


def test_switch_name_suffix_hook_preserves_subdevice_name_and_nanoe_exception() -> None:
    suffix = _class_method(
        ROOT / "custom_components" / "panasonic_ems2" / "switch.py",
        "PanasonicSwitch",
        "_entity_name_suffix",
    )

    regular = _Entity(
        description=_Description(key="0x01", name="Fallback Switch"),
        client=_Client(command_name="電源"),
    )
    nanoe = _Entity(
        description=_Description(key="0x02", name="nanoe 描述"),
        client=_Client(command_name="nanoe"),
    )

    assert suffix(regular) == "子設備電源"
    assert suffix(nanoe) == "nanoe 描述"


def test_range_mixin_prefers_cloud_range_and_falls_back_to_description_options() -> None:
    option_range = _class_method(BASE, "PanasonicRangeMixin", "_get_options_range")
    option_for_value = _class_method(
        BASE,
        "PanasonicRangeMixin",
        "_option_for_value",
        {"get_key_from_dict": _load_top_level_function(BASE, "get_key_from_dict")},
    )

    cloud = _Entity(
        description=_Description(key="0x10", options=["Off"], options_value=["0"]),
        client=_Client(ranges={"0x10": {"Auto": 0, "Strong": 2}}),
    )
    fallback = _Entity(
        description=_Description(key="0x11", options=["關", "開"], options_value=["0", "1"]),
        client=_Client(ranges={}),
    )

    cloud._get_options_range = option_range.__get__(cloud, _Entity)
    fallback._get_options_range = option_range.__get__(fallback, _Entity)

    assert option_range(cloud) == {"Auto": 0, "Strong": 2}
    assert option_for_value(cloud, "2") == "Strong"
    assert option_range(fallback) == {"關": 0, "開": 1}
    assert option_for_value(fallback, 1) == "開"


def test_writable_mixin_sets_device_refreshes_and_writes_state() -> None:
    async_set_device_value = _class_method(
        BASE,
        "PanasonicWritableEntityMixin",
        "async_set_device_value",
        {"asyncio": asyncio},
    )
    entity = _Entity(description=_Description(key="0x20"))

    asyncio.run(async_set_device_value(entity, "3"))

    assert entity.client.set_calls == [("GWID_SHARED", 1, "0x20", 3)]
    assert entity.client.update_calls == [("GWID_SHARED", 1)]
    assert entity.writes == 1


def test_phase2_platforms_reuse_shared_entity_helpers() -> None:
    required_base_classes = {
        "PanasonicDescribedEntity",
        "PanasonicRangeMixin",
        "PanasonicWritableEntityMixin",
    }
    assert required_base_classes <= _class_names(BASE)

    for path in PLATFORM_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert not any(
            isinstance(node, ast.FunctionDef) and node.name == "get_key_from_dict"
            for node in tree.body
        ), path
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not node.name.startswith("Panasonic"):
                continue
            method_names = {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            assert "unique_id" not in method_names, (path, node.name)
            assert "name" not in method_names, (path, node.name)
