"""Shared Panasonic entity description dataclasses."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.number import NumberEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription


@dataclass
class PanasonicBinarySensorDescription(
    BinarySensorEntityDescription
):
    """Class to describe an Panasonic binary sensor."""
    options_value: list[str] | None = None


@dataclass
class PanasonicNumberDescription(
    NumberEntityDescription
):
    """Class to describe an Panasonic number."""
    options_value: list[str] | None = None


@dataclass
class PanasonicSelectDescription(
    SelectEntityDescription
):
    """Class to describe an Panasonic select."""
    options_value: list[str] | None = None


@dataclass
class PanasonicSensorDescription(
    SensorEntityDescription
):
    """Class to describe an Panasonic sensor."""


@dataclass
class PanasonicSwitchDescription(
    SwitchEntityDescription
):
    """Class to describe an Panasonic switch."""
    reverse_state: bool = False
