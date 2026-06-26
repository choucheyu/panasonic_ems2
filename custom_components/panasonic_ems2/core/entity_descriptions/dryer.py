"""Dryer entity descriptions."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    EntityCategory,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)

from ..constants.common import (
    ENTITY_EMPTY,
    ENTITY_UPDATE,
)
from ..constants.dryer import (
    DRYER_POWER,
    DRYER_OPERATING_STATUS,
    DRYER_HEATING_STATUS,
    DRYER_OPERATING_MODE,
    DRYER_OPERATING_TIME,
    DRYER_REMAINING_TIME,
    DRYER_STATUS,
    DRYER_DISPLAY,
    DRYER_FAN_SPEED,
    DRYER_TEMPERATURE,
    DRYER_ERROR_CODE,
    DRYER_ENERGY,
    DRYER_APPOINTMENT_REMAINING_TIME,
    DRYER_PROGRAM_1,
    DRYER_OPERATING_STATUS_NEW,
    DRYER_OPERATING_MODE_NEW,
    DRYER_PROGRAM_2,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

DRYER_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
    PanasonicBinarySensorDescription(
        key=ENTITY_UPDATE,
        name="版本更新",
        icon='mdi:package-up',
        device_class=BinarySensorDeviceClass.UPDATE
    ),
    PanasonicBinarySensorDescription(
        key=ENTITY_EMPTY,
        name="空",
        icon='mdi:cog'
    )
)

DRYER_NUMBERS: tuple[PanasonicNumberDescription, ...] = (
    PanasonicNumberDescription(
        key=DRYER_OPERATING_TIME,
        name="運轉時間",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=12,
        native_step=1,
        entity_registry_enabled_default=False
    )
)

DRYER_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=DRYER_OPERATING_STATUS,
        name="運轉狀態",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:cog',
        options=["Stopping", "Pause", "Working"],
        options_value=["0", "1", "2"]
    ),
    PanasonicSelectDescription(
        key=DRYER_HEATING_STATUS,
        name="加熱狀態",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:cog',
        options=["Weak", "Strong"],
        options_value=["0", "1"]
    ),
    PanasonicSelectDescription(
        key=DRYER_OPERATING_MODE,
        name="運轉模式",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:hanger',
        options=["Standard", "Thick Clothes", "Long Time", "Short Time", "Reserved"],
        options_value=["0", "1", "2", "3", "4"]
    ),
    PanasonicSelectDescription(
        key=DRYER_OPERATING_MODE_NEW,
        name="運轉模式",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:hanger'
    ),
    PanasonicSelectDescription(
        key=DRYER_STATUS,
        name="烘乾狀態",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:cog',
        options=["Fan Only", "Drying"],
        options_value=["0", "1"]
    ),
    PanasonicSelectDescription(
        key=DRYER_FAN_SPEED,
        name="風速",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan',
        options=["Low", "Middle", "High"],
        options_value=["0", "1", "2", "3"],
    )
)

DRYER_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=DRYER_OPERATING_STATUS_NEW,
        name="運轉狀態",
        icon="mdi:tumble-dryer"
    ),
    PanasonicSensorDescription(
        key=DRYER_APPOINTMENT_REMAINING_TIME,
        name="剩餘時間",
        icon="mdi:timer-outline"
    ),
    PanasonicSensorDescription(
        key=DRYER_ERROR_CODE,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    )
)
