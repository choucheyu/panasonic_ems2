"""Washing machine entity descriptions."""

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
    ENTITY_WASH_TIMES,
    ENTITY_WATER_USED,
)
from ..constants.washing_machine import (
    WASHING_MACHINE_POWER,
    WASHING_MACHINE_ENABLE,
    WASHING_MACHINE_PROGRESS,
    WASHING_MACHINE_OPERATING_STATUS_OLD,
    WASHING_MACHINE_REMAING_WASH_TIME,
    WASHING_MACHINE_TIMER,
    WASHING_MACHINE_TIMER_REMAINING_TIME_OLD,
    WASHING_MACHINE_ERROR_CODE,
    WASHING_MACHINE_ERROR_STATUS,
    WASHING_MACHINE_PROGRAM_1,
    WASHING_MACHINE_LX128_REMAINING_WASH_TIME,
    WASHING_MACHINE_NANOE_REMAINING_TIME,
    WASHING_MACHINE_ENERGY,
    WASHING_MACHINE_OPERATING_STATUS,
    WASHING_MACHINE_51,
    WASHING_MACHINE_52,
    WASHING_MACHINE_53,
    WASHING_MACHINE_CURRENT_MODE,
    WASHING_MACHINE_CURRENT_PROGRESS,
    WASHING_MACHINE_POSTPONE_DRYING,
    WASHING_MACHINE_57,
    WASHING_MACHINE_TIMER_REMAINING_TIME,
    WASHING_MACHINE_59,
    WASHING_MACHINE_60,
    WASHING_MACHINE_DRYING_TIME,
    WASHING_MACHINE_DRYING_METHOD,
    WASHING_MACHINE_61,
    WASHING_MACHINE_POSTPONE_DRYING_TIME,
    WASHING_MACHINE_PROGRESS_NEW,
    WASHING_MACHINE_66,
    WASHING_MACHINE_67,
    WASHING_MACHINE_68,
    WASHING_MACHINE_WARM_WATER,
    WASHING_MACHINE_71,
    WASHING_MACHINE_72,
    WASHING_MACHINE_73,
    WASHING_MACHINE_REMOTE_CONTROL,
    WASHING_MACHINE_DETERGENT_AMOUNT,
    WASHING_MACHINE_SOFTENER_AMOUNT,
    WASHING_MACHINE_MODELS,
    WASHING_MACHINE_2020_MODELS,
    WASHING_MACHINE_LX128B_COMMANDS,
    WASHING_MACHINE_HDH_COMMANDS,
    WASHING_MACHINE_HDH_NON_COMMANDLIST_COMMANDS,
    WASHING_MACHINE_HDH_SUPPLEMENTAL_COMMANDS,
    WASHING_MACHINE_HDH_SUPPLEMENTAL_DISPLAY_KEYS,
    COMMAND_NAME_OVERRIDES,
    COMMAND_RANGE_OVERRIDES,
    WASHING_MACHINE_CLOCK_TIME_KEYS,
    WASHING_MACHINE_ACTIVE_FINISH_TIME_KEYS,
    WASHING_MACHINE_RESERVATION_CLOCK_TIME_KEYS,
    WASHING_MACHINE_ACTIVE_OPERATING_STATUS_VALUES,
    WASHING_MACHINE_RESERVATION_OPERATING_STATUS_VALUES,
    WASHING_MACHINE_KBS_COMMANDS,

)
from .base import (
    PanasonicBinarySensorDescription,
    PanasonicNumberDescription,
    PanasonicSelectDescription,
    PanasonicSensorDescription,
    PanasonicSwitchDescription,
)

WASHING_MACHINE_BINARY_SENSORS: tuple[PanasonicBinarySensorDescription, ...] = (
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

WASHING_MACHINE_HDH_SELECTS: tuple[PanasonicSelectDescription, ...] = (
    PanasonicSelectDescription(
        key=WASHING_MACHINE_TIMER,
        name="預約時間設定",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:clock-start",
        options=[],
        options_value=[]
    ),
    PanasonicSelectDescription(
        key=WASHING_MACHINE_60,
        name="時間調整",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:clock-edit-outline",
        options=[],
        options_value=[]
    ),
    PanasonicSelectDescription(
        key=WASHING_MACHINE_POSTPONE_DRYING_TIME,
        name="延後晾衣設定",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:hanger",
        options=[],
        options_value=[]
    ),
    PanasonicSelectDescription(
        key=WASHING_MACHINE_PROGRESS_NEW,
        name="行程設定",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:washing-machine",
        options=[],
        options_value=[]
    )
)

WASHING_MACHINE_SELECTS_BY_MODEL = {
    # Only HDH was confirmed against the remote CommandList. Do not apply these
    # writable selects to DDH/DW/MDH until their CommandList/ranges are checked.
    "HDH": WASHING_MACHINE_HDH_SELECTS,
}

WASHING_MACHINE_SELECTS: tuple[PanasonicSelectDescription, ...] = ()

WASHING_MACHINE_DSH_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=WASHING_MACHINE_OPERATING_STATUS_OLD,
        name="工程訊息",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:progress-helper"
    ),
)

WASHING_MACHINE_RPH_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=WASHING_MACHINE_DRYING_TIME,
        name="乾燥時間設定",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:tumble-dryer"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_DRYING_METHOD,
        name="乾燥方法設定",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:tumble-dryer"
    ),
)

WASHING_MACHINE_CN_RW_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=WASHING_MACHINE_PROGRAM_1,
        name="工程資訊",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:progress-helper"
    ),
)

WASHING_MACHINE_LX128_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=WASHING_MACHINE_LX128_REMAINING_WASH_TIME,
        name="洗衣殘時間",
        icon="mdi:clock"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_NANOE_REMAINING_TIME,
        name="nanoe殘時間",
        icon="mdi:atom-variant"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_ERROR_STATUS,
        name="異常狀態",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:alert-circle"
    ),
)

WASHING_MACHINE_SENSORS_BY_MODEL = {
    "DSH": WASHING_MACHINE_DSH_SENSORS,
    "RPH": WASHING_MACHINE_RPH_SENSORS,
    "CN-RW": WASHING_MACHINE_CN_RW_SENSORS,
    "LX128E": WASHING_MACHINE_LX128_SENSORS,
    "LX128F": WASHING_MACHINE_LX128_SENSORS,
    "LX128G": WASHING_MACHINE_LX128_SENSORS,
}

WASHING_MACHINE_SENSORS: tuple[PanasonicSensorDescription, ...] = (
    PanasonicSensorDescription(
        key=WASHING_MACHINE_REMAING_WASH_TIME,
        name="預估洗衣完成時間",
        icon="mdi:clock"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_TIMER,
        name="預約時間設定",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:clock-start"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_TIMER_REMAINING_TIME_OLD,
        name="預約洗衣開始時間",
        icon="mdi:clock-alert-outline"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_TIMER_REMAINING_TIME,
        name="預約洗衣完成時間",
        icon="mdi:clock-outline"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_ERROR_CODE,
        name="異常代碼",
        icon="mdi:alert-circle"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_60,
        name="時間調整",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:clock-edit-outline"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_POSTPONE_DRYING_TIME,
        name="延後晾衣設定",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:hanger"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_CURRENT_MODE,
        name="目前洗衣行程",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:washing-machine"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_CURRENT_PROGRESS,
        name="洗衣行程設定",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:progress-helper"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_PROGRESS_NEW,
        name="行程設定",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:washing-machine"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_POSTPONE_DRYING,
        name="延後晾衣狀態(raw)",
        icon="mdi:hanger"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_OPERATING_STATUS,
        name="運轉情報",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:washing-machine"
    ),
    PanasonicSensorDescription(
        key=ENTITY_WASH_TIMES,
        name="當月洗衣次數",
        icon="mdi:information-slab-symbol"
    ),
    PanasonicSensorDescription(
        key=ENTITY_WATER_USED,
        name="當月用水量",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:water"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_ENERGY,
        name="累積用電量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:flash"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_REMOTE_CONTROL,
        name="遠端遙控",
        device_class=SensorDeviceClass.ENUM,
        icon='mdi:cog'
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_DETERGENT_AMOUNT,
        name="洗劑投入設定",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="mL",
        icon="mdi:bottle-tonic-outline"
    ),
    PanasonicSensorDescription(
        key=WASHING_MACHINE_SOFTENER_AMOUNT,
        name="柔軟劑投入設定",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="mL",
        icon="mdi:bottle-tonic-plus-outline"
    )
)

WASHING_MACHINE_SWITCHES: tuple[PanasonicSwitchDescription, ...] = (
    PanasonicSwitchDescription(
        key=WASHING_MACHINE_ENABLE,
        name="開始洗衣",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:play-pause'
    ),
    PanasonicSwitchDescription(
        key=WASHING_MACHINE_WARM_WATER,
        name="溫水設定",
        device_class=SwitchDeviceClass.SWITCH,
        icon='mdi:heat-wave'
    )
)
