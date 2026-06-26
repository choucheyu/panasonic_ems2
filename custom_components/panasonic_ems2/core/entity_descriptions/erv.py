"""ERV entity descriptions."""

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
from ..constants.erv import (
    ERV_POWER,
    ERV_OPERATING_MODE,
    ERV_FAN_SPEED,
    ERV_TARGET_TEMPERATURE,
    ERV_TEMPERATURE_IN,
    ERV_TEMPERATURE_OUT,
    ERV_TIMER_ON,
    ERV_ERROR_CODE,
    ERV_ENERGY,
    ERV_RESET_FILTER_NOTIFY,
    ERV_VENTILATE_MODE,
    ERV_PRE_HEAT_COOL,
    ERV_REVERED,
    ERV_MINIMUM_TEMPERATURE,
    ERV_MAXIMUM_TEMPERATURE,
    ERV_AVAILABLE_MODES,
    ERV_AVAILABLE_FAN_MODES,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

ERV_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
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

ERV_NUMBERS: tuple[PanasonicNumberDescription, ...] = (
    PanasonicNumberDescription(
        key=ERV_TARGET_TEMPERATURE,
        name="目標溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:thermometer',
        native_min_value=-128,
        native_max_value=127,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=ERV_TIMER_ON,
        name="定時開啟",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=1440,
        native_step=1,
        entity_registry_enabled_default=False
    )
)

ERV_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=ERV_VENTILATE_MODE,
        name="換氣模式",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:home-thermometer',
        options=["Auto", "Ventilate", "Normal"],
        options_value=["0", "1", "2"],
    ),
    PanasonicSelectDescription(
        key=ERV_PRE_HEAT_COOL,
        name="Pre Head/Cool",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:home-thermometer-outline',
        options=["Disabled", "30min", "60min"],
        options_value=["0", "1", "2"]
    )
)

ERV_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=ERV_TEMPERATURE_IN,
        name="進風溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer"
    ),
    PanasonicSensorDescription(
        key=ERV_TEMPERATURE_OUT,
        name="出風溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer"
    ),
    PanasonicSensorDescription(
        key=ERV_ENERGY,
        name="累積用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    ),
    PanasonicSensorDescription(
        key=ERV_ERROR_CODE,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    )
)
