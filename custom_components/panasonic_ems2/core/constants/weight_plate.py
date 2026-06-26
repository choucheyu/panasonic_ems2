"""Weight plate command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility.
"""

from __future__ import annotations

WEIGHT_PLATE_GET_WEIGHT = "0x52"

WEIGHT_PLATE_FOOD_NAME = "0x80"

WEIGHT_PLATE_MANAGEMENT_MODE = "0x81"

WEIGHT_PLATE_MANAGEMENT_VALUE = "0x82"

WEIGHT_PLATE_AMOUNT_MAX = "0x83"

WEIGHT_PLATE_BUY_DATE = "0x84"

WEIGHT_PLATE_DUE_DATE = "0x85"

WEIGHT_PLATE_COMMUNICATION_MODE = "0x8A"

WEIGHT_PLATE_COMMUNICATION_TIME = "0x8B"

WEIGHT_PLATE_TOTAL_WEIGHT = "0x8C"

WEIGHT_PLATE_RESTORE_WEIGHT = "0x8D"

WEIGHT_PLATE_LOW_BATTERY = "0x8E"
