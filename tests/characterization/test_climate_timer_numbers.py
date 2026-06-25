"""Characterize Panasonic climate timer number behavior.

These tests intentionally lock the currently observed integration seam before any
normalization change is attempted. Live devices show active timer values as a
countdown in minutes, while inactive timers may be reported by Panasonic as the
sentinel value 65535 even though HA advertises a 0..1440 number range.
"""

from __future__ import annotations

import ast
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import load_constant_assignments, load_method_function

ROOT = Path(__file__).resolve().parents[2]
CONST = ROOT / "custom_components/panasonic_ems2/core/const.py"
NUMBER = ROOT / "custom_components/panasonic_ems2/number.py"


@dataclass
class _Description:
    key: str


class _Coordinator:
    data = object()


class _Client:
    def __init__(self) -> None:
        self.set_calls: list[tuple[str, int, str, int]] = []
        self.update_calls: list[tuple[str, int]] = []

    async def set_device(self, gwid: str, device_id: int, key: str, value: int) -> None:
        self.set_calls.append((gwid, device_id, key, value))

    async def update_device(self, gwid: str, device_id: int) -> None:
        self.update_calls.append((gwid, device_id))


class _NumberEntity:
    def __init__(self, *, key: str, raw_value: int | str) -> None:
        self.entity_description = _Description(key=key)
        self.coordinator = _Coordinator()
        self.device_gwid = "GWID_TIMER_1"
        self.device_id = 1
        self.client = _Client()
        self.writes = 0
        self._status = {key: raw_value}

    def get_status(self, _data):
        return self._status

    def async_write_ha_state(self) -> None:
        self.writes += 1


def _constants() -> dict[str, Any]:
    return load_constant_assignments(CONST)


def _eval_descriptor_node(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.List):
        return [_eval_descriptor_node(item, env) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_descriptor_node(item, env) for item in node.elts)
    if isinstance(node, ast.Attribute):
        dotted = ast.unparse(node)
        if dotted == "UnitOfTime.MINUTES":
            return "min"
        if dotted == "UnitOfTime.HOURS":
            return "h"
        return dotted
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return {keyword.arg: _eval_descriptor_node(keyword.value, env) for keyword in node.keywords}
    raise TypeError(ast.dump(node))


def _load_climate_number_descriptions() -> tuple[dict[str, Any], ...]:
    env = _constants()
    tree = ast.parse(CONST.read_text(encoding="utf-8"), filename=str(CONST))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "CLIMATE_NUMBERS":
            return _eval_descriptor_node(node.value, env)
    raise AssertionError("CLIMATE_NUMBERS not found")


def test_climate_timer_numbers_are_minutes_with_inactive_sentinel_outside_ha_range() -> None:
    const = _constants()
    timer_on = const["CLIMATE_TIMER_ON"]
    timer_off = const["CLIMATE_TIMER_OFF"]

    assert timer_on == "0x0B"
    assert timer_off == "0x0C"
    assert const["SET_COMMAND_TYPE"][str(const["DEVICE_TYPE_CLIMATE"])][timer_on] == 139
    assert const["SET_COMMAND_TYPE"][str(const["DEVICE_TYPE_CLIMATE"])][timer_off] == 140

    climate_numbers = _load_climate_number_descriptions()
    by_key = {description["key"]: description for description in climate_numbers}

    for key in (timer_on, timer_off):
        description = by_key[key]
        assert description["native_unit_of_measurement"] == "min"
        assert description["native_min_value"] == 0
        assert description["native_max_value"] == 1440
        assert description["native_step"] == 1

    assert 65535 > by_key[timer_on]["native_max_value"]
    assert 65535 > by_key[timer_off]["native_max_value"]


def test_native_value_normalizes_panasonic_65535_timer_sentinel_to_zero_for_ui() -> None:
    const = _constants()
    native_value = load_method_function(
        NUMBER,
        class_name="PanasonicNumber",
        method_name="native_value",
        globals_env={
            "CLIMATE_TIMER_ON": const["CLIMATE_TIMER_ON"],
            "CLIMATE_TIMER_OFF": const["CLIMATE_TIMER_OFF"],
        },
    )

    for key in (const["CLIMATE_TIMER_ON"], const["CLIMATE_TIMER_OFF"]):
        number = _NumberEntity(key=key, raw_value=65535)
        assert native_value(number) == 0.0


def test_native_value_returns_timer_countdown_minutes_as_int_for_clean_ui() -> None:
    const = _constants()
    native_value = load_method_function(
        NUMBER,
        class_name="PanasonicNumber",
        method_name="native_value",
        globals_env={
            "CLIMATE_TIMER_ON": const["CLIMATE_TIMER_ON"],
            "CLIMATE_TIMER_OFF": const["CLIMATE_TIMER_OFF"],
        },
    )

    for raw_value, expected in [(0, 0), ("3", 3), (10, 10)]:
        number = _NumberEntity(key=const["CLIMATE_TIMER_OFF"], raw_value=raw_value)
        value = native_value(number)
        assert value == expected
        assert type(value) is int


def test_setting_timer_number_sends_requested_integer_value_then_refreshes_device() -> None:
    async_set_native_value = load_method_function(
        NUMBER,
        class_name="PanasonicNumber",
        method_name="async_set_native_value",
        globals_env={},
    )
    const = _constants()
    key = const["CLIMATE_TIMER_OFF"]
    number = _NumberEntity(key=key, raw_value=65535)

    asyncio.run(async_set_native_value(number, 10.0))

    assert number.client.set_calls == [("GWID_TIMER_1", 1, key, 10)]
    assert number.client.update_calls == [("GWID_TIMER_1", 1)]
    assert number.writes == 1
