"""Light command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility.
"""

from __future__ import annotations

LIGHT_POWER = "0x00"

LIGHT_PERCENTAGE = "0x01"

LIGHT_OPERATION_STATE = "0x70"

LIGHT_CHANNEL_1_TIMER_ON = "0x71"

LIGHT_CHANNEL_1_TIMER_OFF = "0x72"

LIGHT_MAINTAIN_MODE = "0x73"

LIGHT_CHANNEL_2_TIMER_ON = "0x74"

LIGHT_CHANNEL_2_TIMER_OFF = "0x75"

LIGHT_CHANNEL_3_TIMER_ON = "0x76"

LIGHT_CHANNEL_3_TIMER_OFF = "0x77"

LIGHT_RESERVED = "0x7F"

LIGHT_WTY_COMMANDS = [
#    LIGHT_OPERATION_STATE,
#    LIGHT_CHANNEL_1_TIMER_ON,
#    LIGHT_CHANNEL_1_TIMER_OFF,
    LIGHT_MAINTAIN_MODE,
#    LIGHT_CHANNEL_2_TIMER_ON,
#    LIGHT_CHANNEL_2_TIMER_OFF,
#    LIGHT_CHANNEL_3_TIMER_ON,
#    LIGHT_CHANNEL_3_TIMER_OFF
]
