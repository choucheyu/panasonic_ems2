"""ERV command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility.
"""

from __future__ import annotations

ERV_POWER = "0x00"

ERV_OPERATING_MODE = "0x01"

ERV_FAN_SPEED = "0x02"

ERV_TARGET_TEMPERATURE = "0x03"

ERV_TEMPERATURE_IN = "0x04"

ERV_TEMPERATURE_OUT = "0x05"

ERV_TIMER_ON = "0x06"

ERV_ERROR_CODE = "0x09"

ERV_ENERGY = "0x0E"

ERV_RESET_FILTER_NOTIFY = "0x14"

ERV_VENTILATE_MODE = "0x15"

ERV_PRE_HEAT_COOL = "0x16"

ERV_REVERED = "0x7F"

ERV_MINIMUM_TEMPERATURE = -128

ERV_MAXIMUM_TEMPERATURE = 127

ERV_AVAILABLE_MODES = {
    "Cool": 0,
    "Dehumidify": 1,
    "Fan": 2,
    "Auto": 3,
    "Heat": 4
}

ERV_AVAILABLE_FAN_MODES = {
    "Auto": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "11": 11,
    "12": 12,
    "13": 13,
    "14": 14,
    "15": 15
}
