"""Pure tests for recorder external statistics payload building."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "statistics_builder.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("panasonic_statistics_builder", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_safe_statistic_object_id_keeps_external_ids_stable() -> None:
    builder = _load_builder()

    assert builder.safe_statistic_object_id("GWID-ABC 123") == "gwid_abc_123"
    assert builder.safe_statistic_object_id("__GWID!!") == "gwid"


def test_statistics_start_from_label_supports_day_and_month_buckets() -> None:
    builder = _load_builder()
    timezone = dt.timezone.utc

    assert builder.statistics_start_from_label("2026-06-26", timezone) == dt.datetime(
        2026,
        6,
        26,
        tzinfo=timezone,
    )
    assert builder.statistics_start_from_label("2026-06", timezone) == dt.datetime(
        2026,
        6,
        1,
        tzinfo=timezone,
    )


def test_external_statistics_rows_build_metadata_and_running_sum() -> None:
    builder = _load_builder()
    timezone = dt.timezone.utc

    rows = builder.build_user_info_external_statistics_rows(
        metrics=[
            {
                "gwid": "GWID-CLIMATE 1",
                "suffix": "energy",
                "name": "用電量",
                "unit": "kWh",
                "unit_class": "energy",
                "values": [1.5, 2.0, 3.0],
            }
        ],
        labels=["2026-06-25", "2026-06-26"],
        range_key="last_30_days",
        devices_info={"GWID-CLIMATE 1": {"NickName": "客廳空調"}},
        domain="panasonic_ems2",
        timezone=timezone,
    )

    assert rows == [
        {
            "metadata": {
                "mean_type": "none",
                "has_sum": True,
                "name": "客廳空調 用電量",
                "source": "panasonic_ems2",
                "statistic_id": "panasonic_ems2:gwid_climate_1_energy_day",
                "unit_class": "energy",
                "unit_of_measurement": "kWh",
            },
            "statistics": [
                {"start": dt.datetime(2026, 6, 25, tzinfo=timezone), "state": 1.5, "sum": 1.5},
                {"start": dt.datetime(2026, 6, 26, tzinfo=timezone), "state": 2.0, "sum": 3.5},
            ],
            "range_key": "last_30_days",
        }
    ]


def test_external_statistics_rows_use_month_suffix_and_fallback_device_name() -> None:
    builder = _load_builder()
    timezone = dt.timezone.utc

    rows = builder.build_user_info_external_statistics_rows(
        metrics=[
            {
                "gwid": "GWID_WASHER",
                "suffix": "water",
                "name": "用水量",
                "unit": "L",
                "unit_class": "volume",
                "values": [10.0, 20.0],
            }
        ],
        labels=["2026-05", "2026-06"],
        range_key="last_12_months",
        devices_info={},
        domain="panasonic_ems2",
        timezone=timezone,
    )

    assert rows[0]["metadata"]["name"] == "gwid_washer 用水量"
    assert rows[0]["metadata"]["statistic_id"] == "panasonic_ems2:gwid_washer_water_month"
    assert rows[0]["statistics"][-1]["sum"] == 30.0
    assert rows[0]["statistics"][0]["start"] == dt.datetime(2026, 5, 1, tzinfo=timezone)
