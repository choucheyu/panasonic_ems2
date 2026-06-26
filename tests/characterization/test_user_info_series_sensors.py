"""Characterization tests for Panasonic UserGetInfo external statistics.

These tests are source-level so they can run in the plain local Python
environment without importing Home Assistant.
"""

from __future__ import annotations

import ast
import datetime as dt
import importlib.util
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import (
    eval_literalish,
    load_constant_assignments,
    load_method_function,
)

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"
STATISTICS_BUILDER_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "statistics_builder.py"
USER_INFO_SERIES_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "user_info_series.py"


class FakeStatisticData(dict):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class FakeStatisticMetaData(dict):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class FakeStatisticMeanType:
    NONE = "none"


class FakeEnergyConverter:
    UNIT_CLASS = "energy"


class FakeVolumeConverter:
    UNIT_CLASS = "volume"


def _load_tuple_call_attributes(tuple_name: str) -> dict[str, dict[str, Any]]:
    env = load_constant_assignments(CONST_PATH)
    source = CONST_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CONST_PATH))

    for node in tree.body:
        assigned_names: list[str] = []
        value_node: ast.AST | None = None
        if isinstance(node, ast.Assign):
            assigned_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assigned_names = [node.target.id]
            value_node = node.value
        if tuple_name not in assigned_names:
            continue
        if not isinstance(value_node, ast.Tuple):
            raise AssertionError(f"{tuple_name} should be a tuple")

        descriptions: dict[str, dict[str, Any]] = {}
        for element in value_node.elts:
            if not isinstance(element, ast.Call):
                continue
            attrs: dict[str, Any] = {}
            for keyword in element.keywords:
                if keyword.arg is None:
                    continue
                try:
                    attrs[keyword.arg] = eval_literalish(keyword.value, env)
                except (KeyError, TypeError):
                    attrs[keyword.arg] = ast.unparse(keyword.value)
            if "key" in attrs:
                descriptions[attrs["key"]] = attrs
        return descriptions
    raise AssertionError(f"{tuple_name} not found")


def _load_cloud_method(method_name: str):
    constants = load_constant_assignments(CONST_PATH)
    series_spec = importlib.util.spec_from_file_location("panasonic_user_info_series", USER_INFO_SERIES_PATH)
    assert series_spec is not None and series_spec.loader is not None
    series_module = importlib.util.module_from_spec(series_spec)
    series_spec.loader.exec_module(series_module)
    builder_spec = importlib.util.spec_from_file_location(
        "panasonic_statistics_builder", STATISTICS_BUILDER_PATH
    )
    assert builder_spec is not None and builder_spec.loader is not None
    builder_module = importlib.util.module_from_spec(builder_spec)
    builder_spec.loader.exec_module(builder_module)
    return constants, load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name=method_name,
        globals_env={
            **constants,
            "datetime": dt.datetime,
            "timedelta": dt.timedelta,
            "local_tz": dt.timezone.utc,
            "StatisticData": FakeStatisticData,
            "StatisticMetaData": FakeStatisticMetaData,
            "StatisticMeanType": FakeStatisticMeanType,
            "EnergyConverter": FakeEnergyConverter,
            "VolumeConverter": FakeVolumeConverter,
            "UnitOfEnergy": type("UnitOfEnergy", (), {"KILO_WATT_HOUR": "kWh"}),
            "UnitOfVolume": type("UnitOfVolume", (), {"LITERS": "L"}),
            "DOMAIN": "panasonic_ems2",
            "parse_user_info_series": series_module.parse_user_info_series,
            "build_user_info_external_statistics_rows": (
                builder_module.build_user_info_external_statistics_rows
            ),
        },
    )


def test_device_get_info_energy_labels_are_cumulative_energy() -> None:
    env = load_constant_assignments(CONST_PATH)
    groups = {
        "AIRPURIFIER_SENSORS": [env["AIRPURIFIER_ENERGY"]],
        "CLIMATE_SENSORS": [env["CLIMATE_ENERGY"]],
        "DEHUMIDIFIER_SENSORS": [env["DEHUMIDIFIER_ENERGY"]],
        "ERV_SENSORS": [env["ERV_ENERGY"]],
        "FRIDGE_SENSORS": [env["FRIDGE_ENERGY"]],
        "WASHING_MACHINE_SENSORS": [env["WASHING_MACHINE_ENERGY"]],
    }

    for group, keys in groups.items():
        descriptions = _load_tuple_call_attributes(group)
        for key in keys:
            assert descriptions[key]["name"] == "累積用電量"


def test_first_round_chart_sensor_entities_are_not_created() -> None:
    constants = load_constant_assignments(CONST_PATH)

    assert "USER_INFO_POWER_SERIES_SENSORS" not in constants
    assert "USER_INFO_WASHER_SERIES_SENSORS" not in constants


def test_user_info_statistics_queries_use_day_and_month_ranges() -> None:
    _, build_requests = _load_cloud_method("_user_info_statistics_requests")

    requests = build_requests(None, dt.datetime(2026, 6, 26, 12, 0))
    by_range = {request["range_key"]: request for request in requests}

    assert by_range["today"]["data"] == {
        "name": "",
        "from": "2026/06/26",
        "unit": "day",
        "max_num": 1,
    }
    assert by_range["current_month"]["data"] == {
        "name": "",
        "from": "2026/06/01",
        "unit": "day",
        "max_num": 26,
    }
    assert by_range["current_year"]["data"] == {
        "name": "",
        "from": "2026/01/01",
        "unit": "month",
        "max_num": 6,
    }
    assert by_range["last_30_days"]["data"] == {
        "name": "",
        "from": "2026/05/28",
        "unit": "day",
        "max_num": 30,
    }
    assert by_range["last_12_months"]["data"] == {
        "name": "",
        "from": "2025/07/01",
        "unit": "month",
        "max_num": 12,
    }
    assert all(request["data"]["unit"] in {"day", "month"} for request in requests)


def test_external_statistics_rows_keep_power_kwh_unscaled_and_use_running_sum() -> None:
    constants, build_rows = _load_cloud_method("_user_info_external_statistics")

    class Client:
        _devices_info = {
            "GWID_CLIMATE": {
                "DeviceType": str(constants["DEVICE_TYPE_CLIMATE"]),
                "NickName": "客廳空調",
                "Information": [{"DeviceID": 1, "status": {}}],
            },
            "GWID_WASHER": {
                "DeviceType": str(constants["DEVICE_TYPE_WASHING_MACHINE"]),
                "NickName": "後陽台洗衣機",
                "Information": [{"DeviceID": 1, "status": {}}],
            },
        }

    client = Client()
    labels = ["2026-06-25", "2026-06-26"]
    rows = build_rows(
        client,
        "Power",
        "last_30_days",
        labels,
        {
            "GwList": [
                {"GwID": "GWID_CLIMATE", "Total_kwh": "17.50", "kwh": [8.6, 8.9]},
                {"GwID": "GWID_WASHER", "Total_kwh": "3.52", "kwh": [0.0, 3.52]},
            ]
        },
    )

    climate = rows[0]
    assert climate["metadata"]["statistic_id"] == "panasonic_ems2:gwid_climate_energy_day"
    assert climate["metadata"]["name"] == "客廳空調 用電量"
    assert climate["metadata"]["unit_of_measurement"] == "kWh"
    assert climate["statistics"] == [
        {"start": dt.datetime(2026, 6, 25, 0, 0, tzinfo=dt.timezone.utc), "state": 8.6, "sum": 8.6},
        {"start": dt.datetime(2026, 6, 26, 0, 0, tzinfo=dt.timezone.utc), "state": 8.9, "sum": 17.5},
    ]
    assert client._devices_info["GWID_CLIMATE"]["Information"][0]["status"] == {}


def test_external_statistics_rows_cover_washer_water_and_count() -> None:
    constants, build_rows = _load_cloud_method("_user_info_external_statistics")

    class Client:
        _devices_info = {
            "GWID_WASHER": {
                "DeviceType": str(constants["DEVICE_TYPE_WASHING_MACHINE"]),
                "NickName": "後陽台洗衣機",
                "Information": [{"DeviceID": 1, "status": {}}],
            },
        }

    rows = build_rows(
        Client(),
        "Other",
        "current_month",
        ["2026-06-25", "2026-06-26"],
        {
            "GwList": [
                {
                    "GwID": "GWID_WASHER",
                    "WM_WaterUsed_Total": 180.0,
                    "WM_WaterUsed": [60.0, 120.0],
                    "WM_WashTime_Total": 2,
                    "WM_WashTime": [1.0, 1.0],
                }
            ]
        },
    )

    by_id = {row["metadata"]["statistic_id"]: row for row in rows}
    water = by_id["panasonic_ems2:gwid_washer_water_day"]
    count = by_id["panasonic_ems2:gwid_washer_wash_count_day"]

    assert water["metadata"]["unit_of_measurement"] == "L"
    assert water["statistics"][-1]["sum"] == 180.0
    assert count["metadata"]["unit_of_measurement"] == "次"
    assert count["statistics"][-1]["sum"] == 2.0
