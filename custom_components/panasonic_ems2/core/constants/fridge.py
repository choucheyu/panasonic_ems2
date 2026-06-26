"""Fridge command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility.
"""

from __future__ import annotations

FRIDGE_FREEZER_MODE = "0x00"

FRIDGE_CHAMBER_MODE = "0x01"

FRIDGE_FREEZER_TEMPERATURE = "0x03"

FRIDGE_CHAMBER_TEMPERATURE = "0x05"

FRIDGE_ECO = "0x0C"

FRIDGE_ERROR_CODE = "0x0E"

FRIDGE_ENERGY = "0x13"

FRIDGE_DEFROST_SETTING = "0x50"

FRIDGE_STOP_ICE_MAKING = "0x52"

FRIDGE_FAST_ICE_MAKING = "0x53"

FRIDGE_FRESH_QUICK_FREZZE = "0x56"

FRIDGE_THAW_MODE = "0x57"

FRIDGE_THAW_TEMPERATURE = "0x58"

FRIDGE_WINTER_MDOE = "0x5A"

FRIDGE_SHOPPING_MODE = "0x5B"

FRIDGE_GO_OUT_MODE = "0x5C"

FRIDGE_NANOEX = "0x61"

FRIDGE_ERROR_CODE_JP = "0x63"

FRIDGE_XGS_COMMANDS = [
                FRIDGE_ECO,
                FRIDGE_FREEZER_TEMPERATURE,
                FRIDGE_CHAMBER_TEMPERATURE,
                FRIDGE_THAW_TEMPERATURE,
                FRIDGE_ENERGY,
                FRIDGE_NANOEX
            ]

FRIDGE_MODELS = [
    "NR-F655WX-X1", "NR-F655WX-X", "NR-F655WPX"
]

FRIDGE_2020_MODELS = [
    "NR-F506HX-N1", "NR-F506HX-W1", "NR-F506HX-X1", "NR-F556HX-N1",
    "NR-F556HX-W1", "NR-F556HX-X1", "NR-F606HX-N1", "NR-F606HX-W1",
    "NR-F606HX-X1", "NR-F656WX-X1"
]
