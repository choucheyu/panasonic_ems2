"""Weight plate entity descriptions."""

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

from ..constants.weight_plate import (
    WEIGHT_PLATE_GET_WEIGHT,
    WEIGHT_PLATE_FOOD_NAME,
    WEIGHT_PLATE_MANAGEMENT_MODE,
    WEIGHT_PLATE_MANAGEMENT_VALUE,
    WEIGHT_PLATE_AMOUNT_MAX,
    WEIGHT_PLATE_BUY_DATE,
    WEIGHT_PLATE_DUE_DATE,
    WEIGHT_PLATE_COMMUNICATION_MODE,
    WEIGHT_PLATE_COMMUNICATION_TIME,
    WEIGHT_PLATE_TOTAL_WEIGHT,
    WEIGHT_PLATE_RESTORE_WEIGHT,
    WEIGHT_PLATE_LOW_BATTERY,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

WEIGHT_PLATE_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_FOOD_NAME,
        name="食材名稱",
        icon="mdi:food"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_BUY_DATE,
        name="購買日期",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_DUE_DATE,
        name="到期日",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_MANAGEMENT_MODE,
        name="Management Mode",
        icon="mdi:cog"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_MANAGEMENT_VALUE,
        name="Management Value",
        icon="mdi:cog"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_AMOUNT_MAX,
        name="最大數值",
        icon="mdi:cog"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_COMMUNICATION_MODE,
        name="Communication Mode",
        icon="mdi:cog"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_COMMUNICATION_TIME,
        name="Communication Time",
        icon="mdi:clock-outline"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_TOTAL_WEIGHT,
        name="總重量",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weight-gram"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_RESTORE_WEIGHT,
        name="還原重量",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weight-gram"
    ),
    PanasonicSensorDescription(
        key=WEIGHT_PLATE_LOW_BATTERY,
        name="低電量",
        icon="mdi:battery-alert"
    )
)
