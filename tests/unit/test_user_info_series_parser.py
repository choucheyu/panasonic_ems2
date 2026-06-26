"""Pure tests for Panasonic UserGetInfo series parsing."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERIES_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "user_info_series.py"


def _load_parse_user_info_series():
    spec = importlib.util.spec_from_file_location("panasonic_user_info_series", SERIES_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_user_info_series


def test_power_series_parses_gwid_variants_and_numeric_values() -> None:
    parse_user_info_series = _load_parse_user_info_series()
    devices_info = {
        "GWID_CLIMATE_1": {"DeviceType": "1"},
        "GWID_WASHER_1": {"DeviceType": "3"},
    }
    response = {
        "GwList": [
            {"GwID": "GWID_CLIMATE_1", "kwh": ["1.5", 2, None, "bad", "3"]},
            {"GWID": "GWID_WASHER_1", "kwh": [0, "4.25"]},
            {"GwID": "GWID_UNKNOWN", "kwh": [99]},
        ]
    }

    assert parse_user_info_series(
        "Power",
        response,
        devices_info,
        washing_machine_device_type="3",
    ) == [
        {
            "gwid": "GWID_CLIMATE_1",
            "suffix": "energy",
            "name": "用電量",
            "unit": "kWh",
            "unit_class": "energy",
            "values": [1.5, 2.0, 3.0],
        },
        {
            "gwid": "GWID_WASHER_1",
            "suffix": "energy",
            "name": "用電量",
            "unit": "kWh",
            "unit_class": "energy",
            "values": [0.0, 4.25],
        },
    ]


def test_washer_other_series_parses_water_and_wash_count_only_for_washers() -> None:
    parse_user_info_series = _load_parse_user_info_series()
    devices_info = {
        "GWID_WASHER_1": {"DeviceType": "3"},
        "GWID_FRIDGE_1": {"DeviceType": "4"},
    }
    response = {
        "GwList": [
            {
                "GwID": "GWID_WASHER_1",
                "WM_WaterUsed": ["10", "bad", 12.5],
                "WM_WashTime": [1, "2", None],
            },
            {
                "GwID": "GWID_FRIDGE_1",
                "WM_WaterUsed": [999],
                "WM_WashTime": [999],
            },
        ]
    }

    assert parse_user_info_series(
        "Other",
        response,
        devices_info,
        washing_machine_device_type="3",
    ) == [
        {
            "gwid": "GWID_WASHER_1",
            "suffix": "water",
            "name": "用水量",
            "unit": "L",
            "unit_class": "volume",
            "values": [10.0, 12.5],
        },
        {
            "gwid": "GWID_WASHER_1",
            "suffix": "wash_count",
            "name": "洗衣次數",
            "unit": "次",
            "unit_class": None,
            "values": [1.0, 2.0],
        },
    ]


def test_user_info_series_ignores_missing_or_malformed_gwlist() -> None:
    parse_user_info_series = _load_parse_user_info_series()

    assert parse_user_info_series("Power", {}, {}, washing_machine_device_type="3") == []
    assert parse_user_info_series(
        "Power",
        {"GwList": "not-a-list"},
        {},
        washing_machine_device_type="3",
    ) == []
