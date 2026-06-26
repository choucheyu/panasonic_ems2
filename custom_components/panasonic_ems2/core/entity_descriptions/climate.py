"""Climate entity descriptions."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    EntityCategory,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfTime,
)

from ..constants.climate import (
    CLIMATE_ACTIVITY,
    CLIMATE_AIRFRESH_MODE,
    CLIMATE_ANTI_MILDEW,
    CLIMATE_AUTO_CLEAN,
    CLIMATE_BOOST,
    CLIMATE_BUZZER,
    CLIMATE_ECO,
    CLIMATE_ENERGY,
    CLIMATE_ERROR_CODE,
    CLIMATE_FAN_SPEED,
    CLIMATE_FUZZY_MODE,
    CLIMATE_HUMIDITY_INDOOR,
    CLIMATE_IMMEDIATE_MILDEW_DRY,
    CLIMATE_INDICATOR_LIGHT,
    CLIMATE_MONITOR_MILDEW,
    CLIMATE_PM25,
    CLIMATE_SLEEP_MODE,
    CLIMATE_SWING_HORIZONTAL_LEVEL,
    CLIMATE_SWING_VERTICAL_LEVEL,

    CLIMATE_TEMPERATURE_INDOOR,
    CLIMATE_TEMPERATURE_OUTDOOR,
    CLIMATE_TIMER_OFF,
    CLIMATE_TIMER_ON,
    CLIMATE_VOICE,
)
from ..constants.common import (
    ENTITY_EMPTY,
    ENTITY_UPDATE,
)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)


CLIMATE_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
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

CLIMATE_NUMBERS: tuple[PanasonicNumberDescription, ...] = (
    PanasonicNumberDescription(
        key=CLIMATE_TIMER_ON,
        name="時間到開",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=1440,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=CLIMATE_TIMER_OFF,
        name="時間到關",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=1440,
        native_step=1,
        entity_registry_enabled_default=False
    )
)

CLIMATE_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=CLIMATE_FUZZY_MODE,
        name="Fuzzy Mode",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:home-thermometer-outline',
        options=["Better", "Too cloud", "Too hot", "Off", "On"],
        options_value=["0", "1", "2", "3", "4"],
    ),
    PanasonicSelectDescription(
        key=CLIMATE_ACTIVITY,
        name="動向感應",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:motion-sensor',
        options=["關", "對人", "不對人", "自動"],
        options_value=["0", "1", "2", "3"]
    ),
    PanasonicSelectDescription(
        key=CLIMATE_INDICATOR_LIGHT,
        name="機體燈光",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:lightbulb',
        options=["亮", "暗", "ECO燈滅"],
        options_value=["0", "1", "2"]
    ),
    PanasonicSelectDescription(
        key=CLIMATE_FAN_SPEED,
        name="風量",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan',
        options=["自動", "1", "2", "3", "4", "5"],
        options_value=["0", "1", "2", "3", "4", "5"]
    ),
    PanasonicSelectDescription(
        key=CLIMATE_SWING_VERTICAL_LEVEL,
        name="上下風向",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan',
        options=["自動", "1", "2", "3", "4"],
        options_value=["0", "1", "2", "3", "4"]
    ),
    PanasonicSelectDescription(
        key=CLIMATE_SWING_HORIZONTAL_LEVEL,
        name="左右風向",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fan',
        options=["自動", "1", "2", "3", "4", "5", "6", "7"],
        options_value=["0", "1", "2", "3", "4", "5", "6", "7"]
    ),
        PanasonicSelectDescription(
        key=CLIMATE_IMMEDIATE_MILDEW_DRY,
        name="立即乾燥防霉",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:weather-dust',
        options=["關閉", "10分鐘行程", "20分鐘行程", "40分鐘行程", "60分鐘行程"],
        options_value=["0", "1", "2", "3", "4"]
    )
)

CLIMATE_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=CLIMATE_TEMPERATURE_INDOOR,
        name="室內溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer"
    ),
    PanasonicSensorDescription(
        key=CLIMATE_ERROR_CODE,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    ),
    PanasonicSensorDescription(
        key=CLIMATE_TEMPERATURE_OUTDOOR,
        name="室外溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer"
    ),
    PanasonicSensorDescription(
        key=CLIMATE_PM25,
        name="PM2.5",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PM25,
        icon="mdi:chemical-weapon"
    ),
    PanasonicSensorDescription(
        key=CLIMATE_ENERGY,
        name="累積用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    ),
        PanasonicSensorDescription(
        key=CLIMATE_HUMIDITY_INDOOR,
        name="室內濕度",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
        icon="mdi:water-percent"
    )
)

CLIMATE_SWITCHES: tuple[PanasonicSwitchDescription, ...] = (
    PanasonicSwitchDescription(
        key=CLIMATE_AIRFRESH_MODE,
        name=" nanoe™ X",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:atom-variant'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_ANTI_MILDEW,
        name="乾燥防霉",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:weather-dust'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_AUTO_CLEAN,
        name="自體淨",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:broom'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_BUZZER,
        name="操作提示音",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:volume-source',
        reverse_state=True
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_MONITOR_MILDEW,
        name="防霉監控",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:mushroom'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_SLEEP_MODE,
        name="睡眠",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:sleep'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_BOOST,
        name="急速",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:rocket-launch'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_ECO,
        name="ECONAVI",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:sprout'
    ),
    PanasonicSwitchDescription(
        key=CLIMATE_VOICE,
        name="聲控開關",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:account-voice'
    )
)
