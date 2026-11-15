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


def _metric(gwid: str, values: list[float], suffix: str = "energy") -> dict:
    return {
        "gwid": gwid,
        "suffix": suffix,
        "name": "用電量",
        "unit": "kWh",
        "unit_class": "energy",
        "values": values,
    }


def test_external_statistics_rows_build_metadata_and_running_sum() -> None:
    builder = _load_builder()
    timezone = dt.timezone.utc

    rows = builder.build_user_info_external_statistics_rows(
        segments=[(["2026-06-25", "2026-06-26"], [_metric("GWID-CLIMATE 1", [1.5, 2.0, 3.0])])],
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
        }
    ]


def test_external_statistics_rows_use_month_suffix_and_fallback_device_name() -> None:
    builder = _load_builder()
    timezone = dt.timezone.utc

    rows = builder.build_user_info_external_statistics_rows(
        segments=[
            (
                ["2026-05", "2026-06"],
                [
                    {
                        "gwid": "GWID_WASHER",
                        "suffix": "water",
                        "name": "用水量",
                        "unit": "L",
                        "unit_class": "volume",
                        "values": [10.0, 20.0],
                    }
                ],
            )
        ],
        devices_info={},
        domain="panasonic_ems2",
        timezone=timezone,
    )

    assert rows[0]["metadata"]["name"] == "gwid_washer 用水量"
    assert rows[0]["metadata"]["statistic_id"] == "panasonic_ems2:gwid_washer_water_month"
    assert rows[0]["statistics"][-1]["sum"] == 30.0
    assert rows[0]["statistics"][0]["start"] == dt.datetime(2026, 5, 1, tzinfo=timezone)


def test_segments_join_into_one_series_with_one_continuous_sum() -> None:
    builder = _load_builder()
    timezone = dt.timezone.utc

    rows = builder.build_user_info_external_statistics_rows(
        segments=[
            (["2026-10-30", "2026-10-31"], [_metric("W", [0.0, 0.5])]),
            (["2026-11-01", "2026-11-02"], [_metric("W", [1.0, 0.25])]),
        ],
        devices_info={},
        domain="panasonic_ems2",
        timezone=timezone,
    )

    assert len(rows) == 1
    stats = rows[0]["statistics"]
    assert [row["start"].date() for row in stats] == [
        dt.date(2026, 10, 30),
        dt.date(2026, 10, 31),
        dt.date(2026, 11, 1),
        dt.date(2026, 11, 2),
    ]
    sums = [row["sum"] for row in stats]
    assert sums == sorted(sums)
    assert round(sums[-1], 2) == 1.75


def test_short_segment_does_not_shift_dates_of_the_next_segment() -> None:
    builder = _load_builder()

    rows = builder.build_user_info_external_statistics_rows(
        segments=[
            (["2026-10-30", "2026-10-31"], [_metric("W", [0.5])]),
            (["2026-11-01"], [_metric("W", [1.0])]),
        ],
        devices_info={},
        domain="panasonic_ems2",
        timezone=dt.timezone.utc,
    )

    stats = rows[0]["statistics"]
    assert [(row["start"].date(), row["state"]) for row in stats] == [
        (dt.date(2026, 10, 30), 0.5),
        (dt.date(2026, 11, 1), 1.0),
    ]


def test_metric_missing_from_a_segment_is_skipped() -> None:
    builder = _load_builder()

    rows = builder.build_user_info_external_statistics_rows(
        segments=[
            (["2026-10-31"], [_metric("A", [1.0])]),
            (["2026-11-01"], [_metric("A", [2.0]), _metric("B", [3.0])]),
        ],
        devices_info={},
        domain="panasonic_ems2",
        timezone=dt.timezone.utc,
    )

    assert [row["metadata"]["statistic_id"] for row in rows] == ["panasonic_ems2:a_energy_day"]


def test_rebase_statistics_continues_an_existing_sum() -> None:
    builder = _load_builder()
    stats = [{"start": 1, "state": 0.2, "sum": 0.2}, {"start": 2, "state": 0.1, "sum": 0.3}]

    rebased = builder.rebase_statistics(stats, 10.0)

    assert [round(row["sum"], 6) for row in rebased] == [10.2, 10.3]
    assert [row["state"] for row in rebased] == [0.2, 0.1]
    assert stats[0]["sum"] == 0.2
