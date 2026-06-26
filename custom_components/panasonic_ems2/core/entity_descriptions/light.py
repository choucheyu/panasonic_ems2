"""Light entity descriptions."""

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
from ..constants.light import (
    LIGHT_POWER,
    LIGHT_PERCENTAGE,
    LIGHT_OPERATION_STATE,
    LIGHT_CHANNEL_1_TIMER_ON,
    LIGHT_CHANNEL_1_TIMER_OFF,
    LIGHT_MAINTAIN_MODE,
    LIGHT_CHANNEL_2_TIMER_ON,
    LIGHT_CHANNEL_2_TIMER_OFF,
    LIGHT_CHANNEL_3_TIMER_ON,
    LIGHT_CHANNEL_3_TIMER_OFF,
    LIGHT_RESERVED,
    LIGHT_WTY_COMMANDS,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

LIGHT_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
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

LIGHT_NUMBERS: tuple[PanasonicNumberDescription, ...] = (
    PanasonicNumberDescription(
        key=LIGHT_CHANNEL_1_TIMER_ON,
        name="頻道1定時開啟",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=LIGHT_CHANNEL_1_TIMER_OFF,
        name="頻道1定時關閉",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=LIGHT_CHANNEL_2_TIMER_ON,
        name="頻道2定時開啟",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=LIGHT_CHANNEL_2_TIMER_OFF,
        name="頻道2定時關閉",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=LIGHT_CHANNEL_3_TIMER_ON,
        name="頻道3定時開啟",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog-outline',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    ),
    PanasonicNumberDescription(
        key=LIGHT_CHANNEL_3_TIMER_OFF,
        name="頻道3定時關閉",
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:timer-cog',
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        entity_registry_enabled_default=False
    )
)

LIGHT_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=LIGHT_OPERATION_STATE,
        name="運作模式",
        icon='mdi:dip-switch',
#        options=["All Off", "Channel 1 On", "Channel 2 On", "Channel 1, 2 On", "Channel 3 On", "Channel 1, 3 On", "Channel 2, 3 On", "All On"],
#        options_value=["0", "1", "2", "3", "4", "5", "6", "7"],
    ),
    PanasonicSensorDescription(
        key=LIGHT_RESERVED,
        name="Reserved",
        icon='mdi:help'
    )
)

LIGHT_SWITCHES: tuple[PanasonicSwitchDescription, ...] = (
    PanasonicSwitchDescription(
        key=LIGHT_POWER,
        name="Switch",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:toggle-switch'
    ),
    PanasonicSwitchDescription(
        key=LIGHT_MAINTAIN_MODE,
        name="Maintain Mode",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        icon='mdi:swap-horizontal'
    ),
    PanasonicSwitchDescription(
        key=LIGHT_RESERVED,
        name="Reserved",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:help'
    )
)
