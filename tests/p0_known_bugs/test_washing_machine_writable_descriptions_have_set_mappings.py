"""P0 guard for writable washing-machine entity descriptions missing set mappings."""

from __future__ import annotations

from typing import cast

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
    )

    missing = sorted(key for key in writable_keys if key not in set_commands)

    assert missing == []


def test_washing_machine_postpone_drying_uses_api_set_command_0x61() -> None:
    """0x56 is the status/UI key, but the command metadata aliases it to set command 0x61."""
    env = _literal_env()
    set_commands = env["SET_COMMAND_TYPE"][str(env["DEVICE_TYPE_WASHING_MACHINE"])]  # type: ignore[index]

    assert set_commands[env["WASHING_MACHINE_POSTPONE_DRYING"]] == int(
        cast(str, env["WASHING_MACHINE_61"]),
        16,
    )
