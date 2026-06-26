"""Climate command and model capability constants.

This module is intentionally Home Assistant independent. ``core.const`` imports
and re-exports these symbols for backward compatibility with existing platform
code and tests.
"""

CLIMATE_POWER = "0x00"
CLIMATE_OPERATING_MODE = "0x01"
CLIMATE_FAN_SPEED = "0x02"
CLIMATE_TARGET_TEMPERATURE = "0x03"
CLIMATE_TEMPERATURE_INDOOR = "0x04"
CLIMATE_SLEEP_MODE = "0x05"
CLIMATE_FUZZY_MODE = "0x07"
CLIMATE_AIRFRESH_MODE = "0x08"
CLIMATE_TIMER_ON = "0x0B"
CLIMATE_TIMER_OFF = "0x0C"
CLIMATE_SWING_VERTICAL = "0x0E"
CLIMATE_SWING_VERTICAL_LEVEL = "0x0F"
CLIMATE_SWING_HORIZONTAL = "0x10"
CLIMATE_SWING_HORIZONTAL_LEVEL = "0x11"
CLIMATE_SET_HUMIDITY = "0x13"
CLIMATE_HUMIDITY_INDOOR = "0x57"
CLIMATE_ERROR_CODE = "0x15"
CLIMATE_ANTI_MILDEW = "0x17"
CLIMATE_AUTO_CLEAN = "0x18"
CLIMATE_ACTIVITY = "0x19"
CLIMATE_BOOST = "0x1A"
CLIMATE_ECO = "0x1B"
CLIMATE_COMFORT = "0x1C"
CLIMATE_BUZZER = "0x1E"
CLIMATE_INDICATOR_LIGHT = "0x1F"
CLIMATE_TEMPERATURE_OUTDOOR = "0x21"
CLIMATE_OPERATING_POWER = "0x27"
CLIMATE_ENERGY = "0x28"
CLIMATE_PM25 = "0x37"
CLIMATE_MONITOR_MILDEW = "0x53"
CLIMATE_IMMEDIATE_MILDEW_DRY = "0x55"
CLIMATE_VOICE = "0x59"
CLIMATE_61 = "0x61"
CLIMATE_RESERVED = "0x7F"
CLIMATE_PRESET_MODE = "0x80"
CLIMATE_SWING_MODE = "0x81"

CLIMATE_RX_COMMANDS = [
                CLIMATE_ERROR_CODE,
                CLIMATE_OPERATING_POWER,
                CLIMATE_PM25,
                CLIMATE_61
]
CLIMATE_PXGD_COMMMANDS = [
]
CLIMATE_PXGD_SUPPLEMENTAL_COMMANDS = [
                CLIMATE_PM25,
            ]
CLIMATE_VX_COMMMANDS = [
            #    CLIMATE_MONITOR_MILDEW,
            #    CLIMATE_IMMEDIATE_MILDEW_DRY,
            #    CLIMATE_HUMIDITY_INDOOR,
            #    CLIMATE_VOICE,
            #    CLIMATE_PM25
]
CLIMATE_UX_COMMMANDS = [
]
CLIMATE_UJ_COMMMANDS = [
]
CLIMATE_UK_COMMMANDS = [
]
# Supplemental read-path checklist for new climate keys:
# 1. define CLIMATE_XXX = "0x.."
# 2. add the key to the appropriate *_SUPPLEMENTAL_COMMANDS list / SUPPLEMENTAL_COMMANDS
# 3. add an entity description in CLIMATE_SENSORS / CLIMATE_SWITCHES / CLIMATE_SELECTS
# 4. if the key is writable, add SET_COMMAND_TYPE mapping (for example 0x53->211, 0x55->213, 0x59->217)
CLIMATE_VX_SUPPLEMENTAL_COMMANDS = [
                CLIMATE_PM25,
                CLIMATE_MONITOR_MILDEW,
                CLIMATE_IMMEDIATE_MILDEW_DRY,
                CLIMATE_HUMIDITY_INDOOR,
                CLIMATE_VOICE,
            ]
CLIMATE_UX_SUPPLEMENTAL_COMMANDS = [
                CLIMATE_PM25,
                CLIMATE_MONITOR_MILDEW,
                CLIMATE_IMMEDIATE_MILDEW_DRY,
                # UX 官方有「室內溫濕度監控」，但目前只有 VX 實機確認 0x57 室內濕度；
                # 待 UX cloud/status snapshot 確認後再啟用，避免產生錯誤濕度 entity。
                # CLIMATE_HUMIDITY_INDOOR,
                CLIMATE_VOICE,
            ]
CLIMATE_UJ_SUPPLEMENTAL_COMMANDS = [
                # UJ 官方有「防霉監控」，但描述為每 24 小時固定啟動，
                # 尚未確認是否等同 VX/UX 的 0x53 可寫開關，先保守關閉。
                # CLIMATE_MONITOR_MILDEW,
                # UJ 官方未列 PM2.5 可視化，先不要啟用 0x37。
                # CLIMATE_PM25,
                # UJ 未確認是否支援 UX/VX 的 10/20/40/60 分鐘立即乾燥防霉 0x55。
                # CLIMATE_IMMEDIATE_MILDEW_DRY,
                # UJ 未確認 0x57 室內濕度與 0x59 聲控開關。
                # CLIMATE_HUMIDITY_INDOOR,
                # CLIMATE_VOICE,
            ]
CLIMATE_UK_SUPPLEMENTAL_COMMANDS = [
                # UK/U 官方僅列防霉監控、自體淨、乾燥防霉等基本清潔功能，
                # 未確認是否有 VX/UX supplemental command；高風險功能先保守關閉。
                # CLIMATE_MONITOR_MILDEW,
                # CLIMATE_PM25,
                # CLIMATE_IMMEDIATE_MILDEW_DRY,
                # CLIMATE_HUMIDITY_INDOOR,
                # CLIMATE_VOICE,
            ]
CLIMATE_PXGD_MODELS = [
    "J-DUCT", "SX-DUCT", "GX", "LJ", "LX", "PX", "QX", "LJV", "PXGD", "VX", "UX", "UJ", "UK", "uk"
]

CLIMATE_PM10_MODELS = [
    "JHW"
]

CLIMATE_PM10_2_MODELS = [
    "JHV2"
]

CLIMATE_PM25_MODELS = [
    "EHW", "GHW", "JHW", "JHV2", "VX", "UX"
]

# Declarative range-family alias for climate option/range lookups.
# When a model_type's metadata lacks a non-empty parameters dict for a given
# command, get_range() falls back to the declared alias model_type. Future
# models can join the same family by adding entries here only.
CLIMATE_RANGE_FAMILY = {
    "VX": {
        CLIMATE_OPERATING_MODE: "PXGD",
        CLIMATE_FAN_SPEED: "PXGD",
    },
    "UX": {
        CLIMATE_OPERATING_MODE: "PXGD",
        CLIMATE_FAN_SPEED: "PXGD",
    },
    "UJ": {
        CLIMATE_OPERATING_MODE: "PXGD",
        CLIMATE_FAN_SPEED: "PXGD",
    },
    "UK": {
        # UK/uk 官方有冷專與冷暖室外機差異；未能從 cloud 判斷前，
        # 先不要借 PXGD 的運轉模式 range，避免冷專機型錯誤暴露「暖氣」。
        # CLIMATE_OPERATING_MODE: "PXGD",
        CLIMATE_FAN_SPEED: "PXGD",
    },
    "uk": {
        # Panasonic cloud 若回傳小寫 uk，同樣先只借風量 range。
        # CLIMATE_OPERATING_MODE: "PXGD",
        CLIMATE_FAN_SPEED: "PXGD",
    },
}
