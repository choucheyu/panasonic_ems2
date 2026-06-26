"""Dehumidifier entity descriptions."""

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
    ENTITY_UPDATE,
)
from ..constants.dehumidifier import (
    DEHUMIDIFIER_POWER,
    DEHUMIDIFIER_MODE,
    DEHUMIDIFIER_TIMER_OFF,
    DEHUMIDIFIER_RELATIVE_HUMIDITY,
    DEHUMIDIFIER_TARGET_HUMIDITY,
    DEHUMIDIFIER_HUMIDITY_INDOOR,
    DEHUMIDIFIER_FAN_SPEED,
    DEHUMIDIFIER_WATER_TANK_STATUS,
    DEHUMIDIFIER_FILTER_CLEAN,
    DEHUMIDIFIER_AIRFRESH_MODE,
    DEHUMIDIFIER_FAN_MODE,
    DEHUMIDIFIER_ERROR_CODE,
    DEHUMIDIFIER_BUZZER,
    DEHUMIDIFIER_ENERGY,
    DEHUMIDIFIER_50,
    DEHUMIDIFIER_51,
    DEHUMIDIFIER_PM25,
    DEHUMIDIFIER_TIMER_ON,
    DEHUMIDIFIER_PM10,
    DEHUMIDIFIER_58,
    DEHUMIDIFIER_59,
    DEHUMIDIFIER_MAX_HUMIDITY,
    DEHUMIDIFIER_MIN_HUMIDITY,
    DEHUMIDIFIER_DEFAULT_MODES,
    DEHUMIDIFIER_PERFORMANCE_MODELS,
    DEHUMIDIFIER_GHW_COMMANDS,
    DEHUMIDIFIER_JHW_COMMANDS,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

DEHUMIDIFIER_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
    PanasonicBinarySensorDescription(
        key=ENTITY_UPDATE,
        name="版本更新",
        icon='mdi:package-up',
        device_class=BinarySensorDeviceClass.UPDATE
    ),
    PanasonicBinarySensorDescription(
        key=DEHUMIDIFIER_WATER_TANK_STATUS,
        name="水箱",
        icon='mdi:cup-water'
    )
)

DEHUMIDIFIER_NUMBERS: tuple[PanasonicNumberDescription, ...] = (
    PanasonicNumberDescription(
        key=DEHUMIDIFIER_TIMER_ON,
        name="定時開啟",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=12,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=DEHUMIDIFIER_TIMER_OFF,
        name="定時關閉",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=12,
        native_step=1,
        entity_registry_enabled_default=False
    )
)

DEHUMIDIFIER_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=DEHUMIDIFIER_FAN_SPEED,
        name="風速",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan',
        options=["Auto", "Slience", "Standard", "Speed"],
        options_value=["0", "1", "2", "3"],
    ),
    PanasonicSelectDescription(
        key=DEHUMIDIFIER_FAN_MODE,
        name="風扇模式",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan-speed-1',
        options=["Fixed", "Down", "Up", "Both", "Side"],
        options_value=["0", "1", "2", "3", "4"]
    )
)

DEHUMIDIFIER_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=DEHUMIDIFIER_HUMIDITY_INDOOR,
        name="室內濕度",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
        icon="mdi:water-percent"
    ),
    PanasonicSensorDescription(
        key=DEHUMIDIFIER_PM10,
        name="PM10",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM10,
        icon="mdi:chemical-weapon"
    ),
    PanasonicSensorDescription(
        key=DEHUMIDIFIER_PM25,
        name="PM2.5",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM25,
        icon="mdi:chemical-weapon"
    ),
    PanasonicSensorDescription(
        key=DEHUMIDIFIER_ENERGY,
        name="累積用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    ),
    PanasonicSensorDescription(
        key=DEHUMIDIFIER_ERROR_CODE,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    )
)

DEHUMIDIFIER_SWITCHES: tuple[PanasonicSwitchDescription, ...] = (
    PanasonicSwitchDescription(
        key=DEHUMIDIFIER_AIRFRESH_MODE,
        name=" nanoe™ X",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:atom-variant'
    ),
    PanasonicSwitchDescription(
        key=DEHUMIDIFIER_BUZZER,
        name="蜂鳴器",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:volume-high'
    )
)
