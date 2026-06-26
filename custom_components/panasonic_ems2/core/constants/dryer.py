"""Dryer command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility.
"""

from __future__ import annotations

DRYER_POWER = "0x00"

DRYER_OPERATING_STATUS = "0x01"

DRYER_HEATING_STATUS = "0x02"

DRYER_OPERATING_MODE = "0x03"

DRYER_OPERATING_TIME = "0x04"

DRYER_REMAINING_TIME = "0x05"

DRYER_STATUS = "0x06"

DRYER_DISPLAY = "0x07"

DRYER_FAN_SPEED = "0x08"

DRYER_TEMPERATURE = "0x09"

DRYER_ERROR_CODE = "0x0A"

DRYER_ENERGY = "0x0F"

DRYER_APPOINTMENT_REMAINING_TIME = "0x15"

DRYER_PROGRAM_1 = "0x34"

DRYER_OPERATING_STATUS_NEW = "0x50"

DRYER_OPERATING_MODE_NEW = "0x55"

DRYER_PROGRAM_2 = "0x64"
