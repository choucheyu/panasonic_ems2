"""P0 guards for washing-machine transient offline/status-empty handling."""

from __future__ import annotations

from pathlib import Path

from tests.helpers.source_parsing import (
    add_capability_runtime_globals,
    load_constant_assignments,
    load_method_function,
)

ROOT = Path(__file__).resolve().parents[2]
CONST_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "const.py"
CLOUD_PATH = ROOT / "custom_components" / "panasonic_ems2" / "core" / "cloud.py"


def _load_offline_info_method():
    constants = add_capability_runtime_globals(load_constant_assignments(CONST_PATH))
    return constants, load_method_function(
        CLOUD_PATH,
        class_name="PanasonicSmartHome",
        method_name="_offline_info",
        globals_env=constants,
    )


def test_washing_machine_offline_info_never_zero_fills_remote_control() -> None:
    """A transient Panasonic status-empty response must not fake 0x74=0."""
    constants, offline_info = _load_offline_info_method()

    info = offline_info(
        None,
        str(constants["DEVICE_TYPE_WASHING_MACHINE"]),
        "HDH",
    )

    assert info == []


def test_status_empty_branch_preserves_existing_washer_information() -> None:
    """The coordinator path must not overwrite previous washer Information with offline zeros."""
    source = CLOUD_PATH.read_text(encoding="utf-8")

    assert 'self._devices_info[gwid]["Information"] = self._offline_info(device_type, model_type)' not in source
    assert 'self._devices_info[gwid].setdefault("Information", [])' in source
    assert "保留上一筆有效 Information" in source
