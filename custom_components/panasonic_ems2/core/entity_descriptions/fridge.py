"""Fridge entity descriptions."""

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
    ENTITY_DOOR_OPENS,
    ENTITY_EMPTY,
    ENTITY_MONTHLY_ENERGY,
    ENTITY_UPDATE,
)
from ..constants.fridge import (
    FRIDGE_FREEZER_MODE,
    FRIDGE_CHAMBER_MODE,
    FRIDGE_FREEZER_TEMPERATURE,
    FRIDGE_CHAMBER_TEMPERATURE,
    FRIDGE_ECO,
    FRIDGE_ERROR_CODE,
    FRIDGE_ENERGY,
    FRIDGE_DEFROST_SETTING,
    FRIDGE_STOP_ICE_MAKING,
    FRIDGE_FAST_ICE_MAKING,
    FRIDGE_FRESH_QUICK_FREZZE,
    FRIDGE_THAW_MODE,
    FRIDGE_THAW_TEMPERATURE,
    FRIDGE_WINTER_MDOE,
    FRIDGE_SHOPPING_MODE,
    FRIDGE_GO_OUT_MODE,
    FRIDGE_NANOEX,
    FRIDGE_ERROR_CODE_JP,
    FRIDGE_XGS_COMMANDS,
    FRIDGE_MODELS,
    FRIDGE_2020_MODELS,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

FRIDGE_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
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

FRIDGE_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=FRIDGE_FREEZER_MODE,
        name="Freezer mode",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fridge-top',
        options=["Weak", "Medium", "Strong"],
        options_value=["0", "2", "4"],
    ),
    PanasonicSelectDescription(
        key=FRIDGE_CHAMBER_MODE,
        name="Chamber Mode",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fridge-bottom',
        options=["Weak", "Medium", "Strong"],
        options_value=["0", "2", "4"],
    ),
    PanasonicSelectDescription(
        key=FRIDGE_THAW_MODE,
        name="Thaw Mode",
        entity_category=EntityCategory.CONFIG,
        icon='mdi:fridge-outline',
        options=["Weak", "Medium", "Strong"],
        options_value=["0", "2", "4"],
    )
)

FRIDGE_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=FRIDGE_FREEZER_TEMPERATURE,
        name="冷凍室溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon='mdi:fridge-top'
    ),
    PanasonicSensorDescription(
        key=FRIDGE_CHAMBER_TEMPERATURE,
        name="冷藏室溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:fridge-bottom"
    ),
    PanasonicSensorDescription(
        key=FRIDGE_ENERGY,
        name="累積用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    ),
    PanasonicSensorDescription(
        key=FRIDGE_THAW_TEMPERATURE,
        name="解凍溫度",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:fridge-outline"
    ),
    PanasonicSensorDescription(
        key=FRIDGE_ERROR_CODE,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    ),
    PanasonicSensorDescription(
        key=FRIDGE_ERROR_CODE_JP,
        name="錯誤代碼",
        icon="mdi:alert-circle"
    ),
    PanasonicSensorDescription(
        key=ENTITY_DOOR_OPENS,
        name="每月開門次數",
        icon="mdi:information-slab-symbol"
    ),
    PanasonicSensorDescription(
        key=ENTITY_MONTHLY_ENERGY,
        name="每月用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    )
)

FRIDGE_SWITCHES: tuple[PanasonicSwitchDescription, ...] = (
    PanasonicSwitchDescription(
        key=FRIDGE_DEFROST_SETTING,
        name=" nanoe™ X",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:snowflake-melt'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_ECO,
        name="ECO",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:sprout'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_NANOEX,
        name=" nanoe™ X",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:atom-variant'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_STOP_ICE_MAKING,
        name="Stop Ice Making",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:snowflake'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_FAST_ICE_MAKING,
        name="Fast Ice Making",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:snowflake'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_FRESH_QUICK_FREZZE,
        name="Fresh Quick Freeze",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:snowflake-check'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_WINTER_MDOE,
        name="Winter Mode",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:snowman'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_SHOPPING_MODE,
        name="採買模式",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:shopping'
    ),
    PanasonicSwitchDescription(
        key=FRIDGE_GO_OUT_MODE,
        name="外出模式",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:logout'
    )
)
