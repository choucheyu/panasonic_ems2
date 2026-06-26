"""P0 guard for writable washing-machine entity descriptions missing set mappings."""

from __future__ import annotations

from tests.p0_known_bugs.test_climate_writable_descriptions_have_set_mappings import (
    _description_keys,
    _literal_env,
)


def test_washing_machine_writable_entity_descriptions_have_explicit_set_mappings() -> None:
    """Fail-closed set_device requires every writable washer entity to be mapped."""
    env = _literal_env()
    set_commands = env["SET_COMMAND_TYPE"][str(env["DEVICE_TYPE_WASHING_MACHINE"])]  # type: ignore[index]
    writable_keys = (
        _description_keys("WASHING_MACHINE_SWITCHES")
        + _description_keys("WASHING_MACHINE_SELECTS")
        + _description_keys("WASHING_MACHINE_HDH_SELECTS")
    )

    missing = sorted(key for key in writable_keys if key not in set_commands)

    assert missing == []


def test_legacy_washing_machine_delay_airing_raw_key_is_not_writable() -> None:
    """0x56 is raw-only; 0x61 is the HDH CommandList-backed setting."""
    env = _literal_env()
    set_commands = env["SET_COMMAND_TYPE"][str(env["DEVICE_TYPE_WASHING_MACHINE"])]  # type: ignore[index]

    assert env["WASHING_MACHINE_POSTPONE_DRYING"] not in set_commands
    assert env["WASHING_MACHINE_POSTPONE_DRYING_TIME"] in set_commands
