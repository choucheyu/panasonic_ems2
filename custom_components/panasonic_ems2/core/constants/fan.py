"""Fan command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility.
"""

from __future__ import annotations

FAN_POWER = "0x00"

FAN_OPERATING_MODE = "0x01"

FAN_SPEED = "0x02"

FAN_TEMPERATURE_INDOOR = "0x03"

FAN_OSCILLATE = "0x05"

FAN_PRESET_MODES = {
    "mode 1": 0,
    "mode 2": 1,
    "mode 3": 2,
    "mode 4": 3,
    "mode 5": 4
}
