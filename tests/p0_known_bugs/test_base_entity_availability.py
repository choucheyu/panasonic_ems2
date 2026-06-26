"""P0 guard for PanasonicBaseEntity availability semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.source_parsing import load_method_function

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "base.py"


class _Entity:
    def __init__(self, *, device_id: int, info: dict, coordinator_data: dict | None = None) -> None:
        self.device_id = device_id
        self.info = info
        self.device_gwid = info.get("GWID", "GWID_TEST")
        self.coordinator = type("Coordinator", (), {"data": coordinator_data or {}})()


def _available(entity: _Entity) -> bool:
    available = load_method_function(
        BASE_PATH,
        class_name="PanasonicBaseEntity",
        method_name="available",
        globals_env={},
    )
    return available(entity)


@pytest.mark.p0_bug
def test_base_entity_availability_honors_matching_device_is_available() -> None:
    """Entity availability must reflect the matched Panasonic sub-device flag."""
    info = {
        "GWID": "GWID_TEST",
        "Devices": [
            {"DeviceID": 1, "IsAvailable": True},
            {"DeviceID": 2, "IsAvailable": False},
        ],
    }

    assert _available(_Entity(device_id=1, info=info)) is True
    assert _available(_Entity(device_id=2, info=info)) is False


@pytest.mark.p0_bug
def test_base_entity_availability_uses_coordinator_data_when_present() -> None:
    """Availability should follow refreshed coordinator data, not stale init info."""
    stale_info = {
        "GWID": "GWID_TEST",
        "Devices": [{"DeviceID": 1, "IsAvailable": True}],
    }
    coordinator_data = {
        "GWID_TEST": {
            "Devices": [{"DeviceID": 1, "IsAvailable": False}],
        }
    }

    assert _available(
        _Entity(device_id=1, info=stale_info, coordinator_data=coordinator_data)
    ) is False


@pytest.mark.p0_bug
def test_base_entity_availability_returns_false_for_missing_sub_device() -> None:
    """Do not report available when Panasonic has no matching sub-device entry."""
    info = {
        "GWID": "GWID_TEST",
        "Devices": [{"DeviceID": 2, "IsAvailable": True}],
    }

    assert _available(_Entity(device_id=1, info=info)) is False
