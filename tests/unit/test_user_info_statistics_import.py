"""UserGetInfo statistics import: one writer per series, continuous sums.

Home Assistant is not installed in the unit-test environment, so the recorder
module is loaded against small stubs of the recorder APIs it calls.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

from tests.helpers.source_parsing import (
    TEST_CORE_PACKAGE,
    _ensure_synthetic_core_package,
    load_constant_assignments,
    load_method_function,
)

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core"
CLOUD_PATH = CORE_PATH / "cloud.py"
UTC = dt.timezone.utc


class FakeRecorder:
    """Stores imported rows and answers statistics_during_period like HA."""

    def __init__(self, rows: dict[str, list[dict[str, Any]]] | None = None) -> None:
        self.rows = rows or {}
        self.queries: list[tuple[str, dt.datetime, dt.datetime]] = []

    def statistics_during_period(self, hass, start_time, end_time, statistic_ids, period, units, types_):
        assert period == "hour" and types_ == {"sum"}
        (statistic_id,) = statistic_ids
        self.queries.append((statistic_id, start_time, end_time))
        found = [
            {"start": row["start"].timestamp(), "sum": row["sum"]}
            for row in sorted(self.rows.get(statistic_id, []), key=lambda row: row["start"])
            if start_time <= row["start"] < end_time
        ]
        return {statistic_id: found} if found else {}

    def async_add_external_statistics(self, hass, metadata, statistics):
        stored = {row["start"]: row for row in self.rows.get(metadata["statistic_id"], [])}
        stored.update({row["start"]: dict(row) for row in statistics})
        self.rows[metadata["statistic_id"]] = list(stored.values())


def _load_recorder_module(monkeypatch, recorder: FakeRecorder):
    class Instance:
        async def async_add_executor_job(self, func, *args):
            return func(*args)

    stubs = {
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.components": types.ModuleType("homeassistant.components"),
        "homeassistant.components.recorder": types.ModuleType("homeassistant.components.recorder"),
        "homeassistant.components.recorder.models": types.ModuleType("homeassistant.components.recorder.models"),
        "homeassistant.components.recorder.statistics": types.ModuleType(
            "homeassistant.components.recorder.statistics"
        ),
        "homeassistant.core": types.ModuleType("homeassistant.core"),
    }
    stubs["homeassistant.components.recorder"].get_instance = lambda hass: Instance()
    stubs["homeassistant.components.recorder.models"].StatisticData = dict
    stubs["homeassistant.components.recorder.statistics"].statistics_during_period = (
        recorder.statistics_during_period
    )
    stubs["homeassistant.components.recorder.statistics"].async_add_external_statistics = (
        recorder.async_add_external_statistics
    )
    stubs["homeassistant.core"].HomeAssistant = object
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)

    _ensure_synthetic_core_package(CORE_PATH)
    name = f"{TEST_CORE_PACKAGE}.statistics_recorder_under_test"
    spec = importlib.util.spec_from_file_location(name, CORE_PATH / "statistics_recorder.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    module.__package__ = TEST_CORE_PACKAGE
    spec.loader.exec_module(module)
    return module


def _day(day: dt.date, state: float, total: float) -> dict[str, Any]:
    return {"start": dt.datetime(day.year, day.month, day.day, tzinfo=UTC), "state": state, "sum": total}


def test_import_series_continues_the_last_sum_before_the_window(monkeypatch) -> None:
    sid = "panasonic_ems2:w_energy_day"
    recorder = FakeRecorder({sid: [_day(dt.date(2026, 9, 30), 0.5, 10.0)]})
    module = _load_recorder_module(monkeypatch, recorder)

    series = [_day(dt.date(2026, 10, 1), 0.0, 0.0), _day(dt.date(2026, 10, 3), 1.0, 1.0)]
    asyncio.run(module.async_import_series(None, {"statistic_id": sid}, series))

    stored = sorted(recorder.rows[sid], key=lambda row: row["start"])
    assert [round(row["sum"], 6) for row in stored] == [10.0, 10.0, 11.0]
    # The lookup must stop before the window, never read the rows it rewrites.
    assert recorder.queries[0][2] == series[0]["start"]


def test_import_series_without_history_starts_at_zero(monkeypatch) -> None:
    sid = "panasonic_ems2:w_energy_day"
    recorder = FakeRecorder()
    module = _load_recorder_module(monkeypatch, recorder)

    asyncio.run(module.async_import_series(None, {"statistic_id": sid}, [_day(dt.date(2026, 11, 1), 1.0, 1.0)]))

    assert recorder.rows[sid][0]["sum"] == 1.0


def test_hourly_refresh_and_month_rollover_keep_the_sum_monotonic(monkeypatch) -> None:
    """Oct+Nov imported, then re-imported, then Nov+Dec after rollover."""
    sid = "panasonic_ems2:w_energy_day"
    recorder = FakeRecorder()
    module = _load_recorder_module(monkeypatch, recorder)

    def window(start: dt.date, values: list[float]) -> list[dict[str, Any]]:
        rows, total = [], 0.0
        for offset, value in enumerate(values):
            total += value
            rows.append(_day(start + dt.timedelta(days=offset), value, total))
        return rows

    october = [0.0] * 30 + [0.5]
    november = [1.0, 0.25, 0.75] + [0.0] * 27
    for _ in range(2):  # the hourly refresh rewrites the same window
        asyncio.run(module.async_import_series(None, {"statistic_id": sid}, window(dt.date(2026, 10, 1), october + november[:15])))
    asyncio.run(module.async_import_series(None, {"statistic_id": sid}, window(dt.date(2026, 11, 1), november + [0.2])))

    stored = sorted(recorder.rows[sid], key=lambda row: row["start"])
    sums = [row["sum"] for row in stored]
    assert all(later >= earlier for earlier, later in zip(sums, sums[1:]))
    assert stored[-1]["start"] == dt.datetime(2026, 12, 1, tzinfo=UTC)
    assert round(sums[-1], 6) == round(sum(october) + sum(november) + 0.2, 6)


def _load_update_method(imports: list):
    constants = load_constant_assignments(CORE_PATH / "const.py")

    class FixedDatetime(dt.datetime):
        @classmethod
        def today(cls):
            return cls(2026, 11, 15, 12, 0)

        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 15, 12, 0, tzinfo=tz)

    async def fake_import_series(hass, metadata, statistics):
        imports.append((metadata["statistic_id"], statistics))

    return load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="_update_user_info_statistics",
        globals_env={
            **constants,
            "datetime": FixedDatetime,
            "local_tz": UTC,
            "apis": types.SimpleNamespace(get_user_info=lambda: "/api/UserGetInfo"),
            "async_import_series": fake_import_series,
        },
    )


class FakeClient:
    def __init__(self, fail: set[tuple[str, str]] | None = None) -> None:
        self.hass = None
        self._user_info_series_last_update = None
        self._devices_info = {"W": {"DeviceType": "3"}}
        self.fail = fail or set()
        self.requests: list[dict[str, Any]] = []

    def _user_info_statistics_requests(self, now):
        return [
            [
                {"range_key": "previous_month", "data": {"from": "2026/10/01", "unit": "day"}, "labels": ["2026-10-31"]},
                {"range_key": "current_month", "data": {"from": "2026/11/01", "unit": "day"}, "labels": ["2026-11-01"]},
            ]
        ]

    async def request(self, method, headers, data, endpoint):
        self.requests.append(dict(data))
        if (data["name"], data["from"]) in self.fail:
            return {}
        return {"GwList": [{"GwID": "W"}]}

    def _user_info_external_statistics(self, info_type, segments):
        return [{"metadata": {"statistic_id": f"{info_type}:{len(segments)}"}, "statistics": [{"sum": 1}]}]


def test_update_writes_each_series_once_from_both_windows() -> None:
    imports: list = []
    update = _load_update_method(imports)
    client = FakeClient()

    assert asyncio.run(update(client, {"CPToken": "t"})) is True

    assert [statistic_id for statistic_id, _ in imports] == ["Power:2", "Other:2"]
    assert len(client.requests) == 4


def test_update_skips_a_series_when_one_window_fails() -> None:
    imports: list = []
    update = _load_update_method(imports)
    client = FakeClient(fail={("Power", "2026/11/01")})

    asyncio.run(update(client, {"CPToken": "t"}))

    assert [statistic_id for statistic_id, _ in imports] == ["Other:2"]
