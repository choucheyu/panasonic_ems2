"""Air purifier entity descriptions."""

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
from ..constants.airpurifier import (
    AIRPURIFIER_POWER,
    AIRPURIFIER_OPERATING_MODE,
    AIRPURIFIER_TIMER_ON,
    AIRPURIFIER_TIMER_OFF,
    AIRPURIFIER_AIR_QUALITY,
    AIRPURIFIER_RESET_FILTER_NOTIFY,
    AIRPURIFIER_HEAP_REPLACE_NOTIFY,
    AIRPURIFIER_NANOEX,
    AIRPURIFIER_LOCK,
    AIRPURIFIER_ERROR_CODE,
    AIRPURIFIER_ENERGY,
    AIRPURIFIER_PM25,
    AIRPURIFIER_51,
    AIRPURIFIER_52,
    AIRPURIFIER_TIMER_OFF_NEW,
    AIRPURIFIER_FORMALDEHYDE,
    AIRPURIFIER_PET_MODE,
    AIRPURIFIER_LIGHT,
    AIRPURIFIER_BUZZER,
    AIRPURIFIER_RUNNING_TIME,
    AIRPURIFIER_RESERVED,
    AIRPURIFIER_NANOEX_PRESET,
    AIRPURIFIER_PRESET_MODES,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

AIRPURIFIER_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
    PanasonicBinarySensorDescription(
        key=ENTITY_UPDATE,
        name="版本更新",
        icon='mdi:package-up',
        device_class=BinarySensorDeviceClass.UPDATE
    ),
    PanasonicBinarySensorDescription(
        key=AIRPURIFIER_HEAP_REPLACE_NOTIFY,
        name="HEAP Filter Replace",
        icon='mdi:filter-variant-remove'
    )
)

AIRPURIFIER_NUMBERS: tuple[PanasonicNumberDescription, ...] = (
    PanasonicNumberDescription(
        key=AIRPURIFIER_TIMER_ON,
        name="定時開啟",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=AIRPURIFIER_TIMER_OFF,
        name="定時關閉",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    )
)

AIRPURIFIER_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=AIRPURIFIER_LIGHT,
        name="燈光",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:brightness-5',
        options=["Light", "Dark", "Off"],
        options_value=["0", "1", "2"]
    ),
    PanasonicSelectDescription(
        key=AIRPURIFIER_OPERATING_MODE,
        name="風扇模式",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan',
        options=["Auto", "Mute", "Week", "Middle", "Strong"],
        options_value=["0", "1", "2", "3", "4"]
    ),
    PanasonicSelectDescription(
        key=AIRPURIFIER_RESERVED,
        name="Reserved",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:help',
        options=[],
        options_value=[]
    )
)

AIRPURIFIER_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=AIRPURIFIER_AIR_QUALITY,
        name="空氣品質",
        device_class= SensorDeviceClass.AQI,
        icon='mdi:leaf'
    ),
    PanasonicSensorDescription(
        key=AIRPURIFIER_PM25,
        name="PM2.5",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM25,
        icon="mdi:chemical-weapon"
    ),
    PanasonicSensorDescription(
        key=AIRPURIFIER_FORMALDEHYDE,
        name="Formaldehyde",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_BILLION,
        state_class=SensorStateClass.MEASUREMENT,
#        device_class=SensorDeviceClass.PM25,
        icon="mdi:chemical-weapon"
    ),
    PanasonicSensorDescription(
        key=AIRPURIFIER_RUNNING_TIME,
        name="運行時間",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clock-outline"
    ),
    PanasonicSensorDescription(
        key=AIRPURIFIER_ERROR_CODE,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    ),
    PanasonicSensorDescription(
        key=AIRPURIFIER_ENERGY,
        name="累積用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    )
)

AIRPURIFIER_SWITCHES: tuple[PanasonicSwitchDescription, ...] = (
    PanasonicSwitchDescription(
        key=AIRPURIFIER_RESET_FILTER_NOTIFY,
        name="Reset Filter Notify",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:filter-remove'
    ),
    PanasonicSwitchDescription(
        key=AIRPURIFIER_BUZZER,
        name="蜂鳴器",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:volume-high'
    ),
    PanasonicSwitchDescription(
        key=AIRPURIFIER_PET_MODE,
        name="寵物模式",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:paw'
    )
)
