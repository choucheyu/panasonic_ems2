# Panasonic EMS2 value source map

> 產生時間：2026-06-26  
> Repo：`/Users/choucheyu/Projects/panasonic_ems2`  
> 依據：目前 working tree 的 `custom_components/panasonic_ems2/core/apis.py`、`core/cloud.py`、`core/const.py`、`sensor.py`、`binary_sensor.py`。  
> 本檔是來源盤點文件；不含 CPToken、RefreshToken、Auth、GWID 完整值等敏感資訊。  
> 注意：hex key 不是全域唯一語意；例如 `0x01` 在不同 device type 代表不同 command。因此下方表格會依設備類型優先列出對應常數名稱。

## 我怎麼知道 key 是從哪個來源來的？

判斷方式不是靠猜，而是看程式把哪個 endpoint 的 response 寫進 `self._devices_info[gwid]["Information"][0]["status"]`：

| 來源 / endpoint | 程式入口 | status 寫入方式 | 用途 |
|---|---|---|---|
| `UserGetRegisteredGwList2` | `apis.get_user_devices()` / `PanasonicSmartHome.get_user_devices()` | 不直接寫 status；寫入 `self._devices` 與 `self._commands`。`self._commands` 之後被 `_refactor_cmds_paras()` 轉成 `CommandName` / `CommandParameters` metadata。 | 取得裝置清單 `GwList` 與遠端 `CommandList` metadata。 |
| `UserGetDeviceStatus` | `apis.get_device_status()` / `get_devices_with_info()` | 只讀簡短狀態 list，取 `0x00`、洗衣機 `0x50`、冰箱 `0x65/0x63` 或第一個非空 `Status` 當作是否需要更新的 gate。 | 判斷設備是否有狀態、是否要進一步打 `DeviceGetInfo`。不是完整 HA entity 來源。 |
| `DeviceGetInfo` main | `apis.post_device_get_info()` / `get_device_with_info()` | 送 `COMMANDS_TYPE + EXTRA_COMMANDS - EXCESS_COMMANDS`，回來的 `devices[].Info[].CommandType/status` 經 `_refactor_info()` 寫入 `Information[].status`。 | 大多數 entity 的主狀態來源。 |
| `DeviceGetInfo` supplemental | `_fetch_device_command_snapshot()` / `_merge_supplemental_status()` | 對 `SUPPLEMENTAL_COMMANDS` 內的 key 另開小包讀；成功才 merge 到既有 `status`。 | 不在遠端 `CommandList`、但實測 targeted read 可取得的 key。 |
| `UserGetInfo` | `apis.get_user_info()` / `get_user_info()` | 對 `USER_INFO_TYPES` 逐項查詢。目前啟用 `Other`，把回傳欄位補進 status，例如 `0xA2/0xA3`。 | 統計/累積資訊，不是 `DeviceGetInfo` command。 |
| `UpdateCheck` | `apis.get_update_info()` / `get_update_info()` | 把更新狀態補進 `0xB0`，版本字串補進 `0xB1`。 | 韌體更新狀態。 |
| `PlateGetMode` | `apis.get_plate_mode()` / `get_plate_info()` | 重量盤專用；把食材/保鮮/重量/電池等欄位補進 `Information[].status`。 | Weight plate 專用額外資料來源。 |
| `_offline_info()` | synthetic fallback | 非洗衣機時可能用 configured command 補 `0`；洗衣機目前刻意回 `[]`，避免 false zero。 | fallback，不是 Panasonic endpoint。 |
| `UserGetGWIP` | `apis.get_gw_ip()` / `get_device_ip()` | 寫入 device dict 的 `GWIP`，不寫 HA `status` key。 | 網路資訊，不是 entity value list。 |
| `DeviceSetCommand` | `apis.set_device()` / `set_device()` | 寫入命令，不是讀取來源。 | 控制設備；不是 value source。 |
| `userlogin1` / `RefreshToken1` / `userlogout1` | login/refresh/logout | 寫 token/session 欄位，不寫 entity status。 | 認證，不是 value source。 |

## 目前有啟用的 `UserGetInfo` list

`USER_INFO_TYPES` 目前只有：

```python
['Other']
```

因此目前會抓 `Other`，不會抓被註解掉的 `Power` / `Temp` / `Humid` / `PM`。程式內雖然保留 `Power` 分支會寫 `0xA0` monthly energy，但因 `USER_INFO_TYPES` 目前未啟用 `Power`，這條路徑不會執行。

### `UserGetInfo` 目前會補進的 status key

| Device type | Key | status 欄位 | 顯示/換算 |
|---|---|---|---|
| Fridge | `0xA1` | `Ref_OpenDoor_Total` | raw 直接顯示。 |
| Washing machine | `0xA3` | `WM_WashTime_Total` | raw 直接顯示：當月洗衣次數。 |
| Washing machine | `0xA2` | `WM_WaterUsed_Total` | raw 直接顯示，sensor 單位 L：當月用水量。 |

### `UserGetInfo` 程式裡存在但目前未啟用的 `Power` 分支

| Device type | Key | status 欄位 | 顯示/換算 |
|---|---|---|---|
| Dehumidifier / Fridge / Washing machine | `0xA0` | `Total_kwh * 0.1` | 程式會先乘 `0.1`；但目前 `USER_INFO_TYPES` 沒有 `Power`，所以不會抓。 |

## `UpdateCheck` 會補進的 status key

| Key | 常數名稱 | 來源欄位 | 顯示/換算 |
|---|---|---|---|
| `0xB0` | `ENTITY_UPDATE` | 有更新時 True；否則 False / cached `_update_info` | binary_sensor，顯示 on/off。 |
| `0xB1` | `ENTITY_UPDATE_INFO` | `UpdateInfo[].updateVersion` | 版本字串；目前 const 裡有常數，但是否有 entity 取決於平台定義。 |

## `UserGetDeviceStatus` 會看的 quick status key

這個 endpoint 不是完整 entity list；目前只用來決定設備是否有狀態、是否要打 `DeviceGetInfo`。

| 判斷順序 | Key | 用途 |
|---|---|---|
| 1 | `0x00` | 一般設備 power/status。 |
| 2 | `0x50` | Washing machine quick operating status。 |
| 3 | `0x65` | Fridge quick status。 |
| 4 | `0x63` | JP Fridge quick status。 |
| 5 | 第一個非空 `Status` | fallback gate。 |

## `DeviceGetInfo` base lists：`COMMANDS_TYPE`

以下是目前 integration 會用來組 main `DeviceGetInfo` 的 base list。實際送出的 main list 還會再加 `EXTRA_COMMANDS` 並扣掉 `EXCESS_COMMANDS`。

### DeviceGetInfo base: `8` — AIRPURIFIER / 空氣清淨機

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `AIRPURIFIER_POWER` |
| `0x01` | `AIRPURIFIER_OPERATING_MODE` |
| `0x0E` | `AIRPURIFIER_ENERGY` |
| `0x06` | `AIRPURIFIER_HEAP_REPLACE_NOTIFY` |
| `0x07` | `AIRPURIFIER_NANOEX` |
| `0x55` | `AIRPURIFIER_PET_MODE` |
| `0x57` | `AIRPURIFIER_BUZZER` |
| `0x50` | `AIRPURIFIER_PM25` |
| `0x56` | `AIRPURIFIER_LIGHT` |
| `0x51` | `AIRPURIFIER_51` |
| `0x52` | `AIRPURIFIER_52` |
| `0x53` | `AIRPURIFIER_TIMER_OFF_NEW` |
| `0x54` | `AIRPURIFIER_FORMALDEHYDE` |

### DeviceGetInfo base: `1` — CLIMATE / 空調

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `CLIMATE_POWER` |
| `0x01` | `CLIMATE_OPERATING_MODE` |
| `0x02` | `CLIMATE_FAN_SPEED` |
| `0x03` | `CLIMATE_TARGET_TEMPERATURE` |
| `0x04` | `CLIMATE_TEMPERATURE_INDOOR` |
| `0x05` | `CLIMATE_SLEEP_MODE` |
| `0x08` | `CLIMATE_AIRFRESH_MODE` |
| `0x0B` | `CLIMATE_TIMER_ON` |
| `0x0C` | `CLIMATE_TIMER_OFF` |
| `0x0F` | `CLIMATE_SWING_VERTICAL_LEVEL` |
| `0x11` | `CLIMATE_SWING_HORIZONTAL_LEVEL` |
| `0x17` | `CLIMATE_ANTI_MILDEW` |
| `0x18` | `CLIMATE_AUTO_CLEAN` |
| `0x19` | `CLIMATE_ACTIVITY` |
| `0x1A` | `CLIMATE_BOOST` |
| `0x1B` | `CLIMATE_ECO` |
| `0x1E` | `CLIMATE_BUZZER` |
| `0x1F` | `CLIMATE_INDICATOR_LIGHT` |
| `0x28` | `CLIMATE_ENERGY` |
| `0x21` | `CLIMATE_TEMPERATURE_OUTDOOR` |

### DeviceGetInfo base: `4` — DEHUMIDIFIER / 除濕機

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `DEHUMIDIFIER_POWER` |
| `0x01` | `DEHUMIDIFIER_MODE` |
| `0x02` | `DEHUMIDIFIER_TIMER_OFF` |
| `0x04` | `DEHUMIDIFIER_TARGET_HUMIDITY` |
| `0x07` | `DEHUMIDIFIER_HUMIDITY_INDOOR` |
| `0x09` | `DEHUMIDIFIER_FAN_SPEED` |
| `0x0A` | `DEHUMIDIFIER_WATER_TANK_STATUS` |
| `0x0D` | `DEHUMIDIFIER_AIRFRESH_MODE` |
| `0x0E` | `DEHUMIDIFIER_FAN_MODE` |
| `0x18` | `DEHUMIDIFIER_BUZZER` |
| `0x1D` | `DEHUMIDIFIER_ENERGY` |
| `0x50` | `DEHUMIDIFIER_50` |
| `0x55` | `DEHUMIDIFIER_TIMER_ON` |

### DeviceGetInfo base: `6` — DRYER / 乾衣機

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `DRYER_POWER` |
| `0x01` | `DRYER_OPERATING_STATUS` |
| `0x09` | `DRYER_TEMPERATURE` |
| `0x15` | `DRYER_APPOINTMENT_REMAINING_TIME` |
| `0x02` | `DRYER_HEATING_STATUS` |
| `0x03` | `DRYER_OPERATING_MODE` |
| `0x04` | `DRYER_OPERATING_TIME` |
| `0x05` | `DRYER_REMAINING_TIME` |
| `0x06` | `DRYER_STATUS` |
| `0x08` | `DRYER_FAN_SPEED` |
| `0x50` | `DRYER_OPERATING_STATUS_NEW` |
| `0x55` | `DRYER_OPERATING_MODE_NEW` |

### DeviceGetInfo base: `14` — ERV / 全熱交換器

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `ERV_POWER` |
| `0x01` | `ERV_OPERATING_MODE` |
| `0x02` | `ERV_FAN_SPEED` |
| `0x03` | `ERV_TARGET_TEMPERATURE` |
| `0x04` | `ERV_TEMPERATURE_IN` |
| `0x05` | `ERV_TEMPERATURE_OUT` |
| `0x09` | `ERV_ERROR_CODE` |
| `0x0E` | `ERV_ENERGY` |

### DeviceGetInfo base: `2` — FRIDGE / 冰箱

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `FRIDGE_FREEZER_MODE` |
| `0x01` | `FRIDGE_CHAMBER_MODE` |
| `0x50` | `FRIDGE_DEFROST_SETTING` |
| `0x52` | `FRIDGE_STOP_ICE_MAKING` |
| `0x53` | `FRIDGE_FAST_ICE_MAKING` |
| `0x56` | `FRIDGE_FRESH_QUICK_FREZZE` |
| `0x57` | `FRIDGE_THAW_MODE` |
| `0x5A` | `FRIDGE_WINTER_MDOE` |
| `0x5B` | `FRIDGE_SHOPPING_MODE` |
| `0x5C` | `FRIDGE_GO_OUT_MODE` |

### DeviceGetInfo base: `17` — LIGHT / 燈具

| Key | 對應常數名稱 |
|---|---|
| `0x00` | `LIGHT_POWER` |

### DeviceGetInfo base: `3` — WASHING_MACHINE / 洗衣機

| Key | 對應常數名稱 |
|---|---|
| `0x01` | `WASHING_MACHINE_ENABLE` |
| `0x13` | `WASHING_MACHINE_REMAING_WASH_TIME` |
| `0x14` | `WASHING_MACHINE_TIMER` |
| `0x19` | `WASHING_MACHINE_ERROR_CODE` |
| `0x58` | `WASHING_MACHINE_TIMER_REMAINING_TIME` |
| `0x1E` | `WASHING_MACHINE_ENERGY` |
| `0x50` | `WASHING_MACHINE_OPERATING_STATUS` |
| `0x54` | `WASHING_MACHINE_CURRENT_MODE` |
| `0x55` | `WASHING_MACHINE_CURRENT_PROGRESS` |
| `0x56` | `WASHING_MACHINE_POSTPONE_DRYING` |
| `0x69` | `WASHING_MACHINE_WARM_WATER` |
| `0x52` | `WASHING_MACHINE_52` |
| `0x66` | `WASHING_MACHINE_66` |
| `0x67` | `WASHING_MACHINE_67` |
| `0x74` | `WASHING_MACHINE_REMOTE_CONTROL` |
| `0x76` | `WASHING_MACHINE_DETERGENT_AMOUNT` |
| `0x77` | `WASHING_MACHINE_SOFTENER_AMOUNT` |

### DeviceGetInfo base: `23` — WEIGHT_PLATE / 重量盤

| Key | 對應常數名稱 |
|---|---|
| `0x52` | `WEIGHT_PLATE_GET_WEIGHT` |


## `DeviceGetInfo` model extras：`EXTRA_COMMANDS`

### EXTRA_COMMANDS: `1` — CLIMATE / 空調

| ModelType | Keys |
|---|---|
| `VX` |  |
| `UX` |  |
| `UJ` |  |
| `UK` |  |
| `uk` |  |
| `RX-N` | `0x15` (CLIMATE_ERROR_CODE), `0x27` (CLIMATE_OPERATING_POWER), `0x37` (CLIMATE_PM25), `0x61` (CLIMATE_61) |
| `RX-G` | `0x15` (CLIMATE_ERROR_CODE), `0x27` (CLIMATE_OPERATING_POWER), `0x37` (CLIMATE_PM25), `0x61` (CLIMATE_61) |
| `RX-J` | `0x15` (CLIMATE_ERROR_CODE), `0x27` (CLIMATE_OPERATING_POWER), `0x37` (CLIMATE_PM25), `0x61` (CLIMATE_61) |

### EXTRA_COMMANDS: `4` — DEHUMIDIFIER / 除濕機

| ModelType | Keys |
|---|---|
| `JHW` | `0x12` (DEHUMIDIFIER_ERROR_CODE), `0x53` (DEHUMIDIFIER_PM25), `0x56` (DEHUMIDIFIER_PM10), `0x58` (DEHUMIDIFIER_58) |

### EXTRA_COMMANDS: `14` — ERV / 全熱交換器

_（空）_

### EXTRA_COMMANDS: `6` — DRYER / 乾衣機

_（空）_

### EXTRA_COMMANDS: `2` — FRIDGE / 冰箱

| ModelType | Keys |
|---|---|
| `XGS` | `0x0C` (FRIDGE_ECO), `0x03` (FRIDGE_FREEZER_TEMPERATURE), `0x05` (FRIDGE_CHAMBER_TEMPERATURE), `0x58` (FRIDGE_THAW_TEMPERATURE), `0x13` (FRIDGE_ENERGY), `0x61` (FRIDGE_NANOEX) |
| `F655` | `0x63` (FRIDGE_ERROR_CODE_JP) |
| `F656` | `0x63` (FRIDGE_ERROR_CODE_JP) |
| `F657` | `0x63` (FRIDGE_ERROR_CODE_JP) |
| `F658` | `0x63` (FRIDGE_ERROR_CODE_JP) |
| `F659` | `0x63` (FRIDGE_ERROR_CODE_JP) |

### EXTRA_COMMANDS: `17` — LIGHT / 燈具

| ModelType | Keys |
|---|---|
| `WTY` | `0x73` (LIGHT_MAINTAIN_MODE) |

### EXTRA_COMMANDS: `3` — WASHING_MACHINE / 洗衣機

| ModelType | Keys |
|---|---|
| `LX128B` | `0x71` (WASHING_MACHINE_71), `0x72` (WASHING_MACHINE_72), `0x73` (WASHING_MACHINE_73) |
| `HDH` | `0x15` (WASHING_MACHINE_TIMER_REMAINING_TIME_OLD), `0x60` (WASHING_MACHINE_60), `0x61` (WASHING_MACHINE_61, WASHING_MACHINE_POSTPONE_DRYING_TIME), `0x64` (WASHING_MACHINE_PROGRESS_NEW) |
| `KBS` | `0x15` (WASHING_MACHINE_TIMER_REMAINING_TIME_OLD) |
| `LM` | `0x15` (WASHING_MACHINE_TIMER_REMAINING_TIME_OLD) |
| `LMS` | `0x15` (WASHING_MACHINE_TIMER_REMAINING_TIME_OLD) |

### EXTRA_COMMANDS: `8` — AIRPURIFIER / 空氣清淨機

_（空）_


## `DeviceGetInfo` model exclusions：`EXCESS_COMMANDS`

### EXCESS_COMMANDS: `1` — CLIMATE / 空調

| ModelType | Keys |
|---|---|
| `J-DUCT` | `0x0F` (CLIMATE_SWING_VERTICAL_LEVEL), `0x11` (CLIMATE_SWING_HORIZONTAL_LEVEL) |

### EXCESS_COMMANDS: `4` — DEHUMIDIFIER / 除濕機

_（空）_

### EXCESS_COMMANDS: `14` — ERV / 全熱交換器

_（空）_

### EXCESS_COMMANDS: `6` — DRYER / 乾衣機

_（空）_

### EXCESS_COMMANDS: `2` — FRIDGE / 冰箱

_（空）_

### EXCESS_COMMANDS: `17` — LIGHT / 燈具

_（空）_

### EXCESS_COMMANDS: `3` — WASHING_MACHINE / 洗衣機

| ModelType | Keys |
|---|---|
| `HDH` | `0x58` (WASHING_MACHINE_TIMER_REMAINING_TIME), `0x1E` (WASHING_MACHINE_ENERGY), `0x56` (WASHING_MACHINE_POSTPONE_DRYING), `0x52` (WASHING_MACHINE_52), `0x66` (WASHING_MACHINE_66), `0x67` (WASHING_MACHINE_67), `0x74` (WASHING_MACHINE_REMOTE_CONTROL), `0x76` (WASHING_MACHINE_DETERGENT_AMOUNT), `0x77` (WASHING_MACHINE_SOFTENER_AMOUNT) |

### EXCESS_COMMANDS: `8` — AIRPURIFIER / 空氣清淨機

_（空）_


## `DeviceGetInfo` supplemental lists：`SUPPLEMENTAL_COMMANDS`

這些 key 不放 main batch；會用 `_fetch_device_command_snapshot()` 分開讀，成功才 merge。

### SUPPLEMENTAL_COMMANDS: `1` — CLIMATE / 空調

| ModelType | Keys |
|---|---|
| `PXGD` | `0x37` (CLIMATE_PM25) |
| `VX` | `0x37` (CLIMATE_PM25), `0x53` (CLIMATE_MONITOR_MILDEW), `0x55` (CLIMATE_IMMEDIATE_MILDEW_DRY), `0x57` (CLIMATE_HUMIDITY_INDOOR), `0x59` (CLIMATE_VOICE) |
| `UX` | `0x37` (CLIMATE_PM25), `0x53` (CLIMATE_MONITOR_MILDEW), `0x55` (CLIMATE_IMMEDIATE_MILDEW_DRY), `0x59` (CLIMATE_VOICE) |
| `UJ` |  |
| `UK` |  |
| `uk` |  |

### SUPPLEMENTAL_COMMANDS: `3` — WASHING_MACHINE / 洗衣機

| ModelType | Keys |
|---|---|
| `HDH` | `0x58` (WASHING_MACHINE_TIMER_REMAINING_TIME), `0x1E` (WASHING_MACHINE_ENERGY), `0x74` (WASHING_MACHINE_REMOTE_CONTROL), `0x76` (WASHING_MACHINE_DETERGENT_AMOUNT), `0x77` (WASHING_MACHINE_SOFTENER_AMOUNT) |


## HDH / NA-V160HDH 目前實際分類

### HDH main `DeviceGetInfo` list

這 12 個是依 `UserGetRegisteredGwList2` 遠端 `CommandList` 確認的主包 key：

| Key | 對應常數名稱 | HA 平台 | 顯示名稱 | 顯示/換算 |
|---|---|---|---|---|
| `0x01` | `WASHING_MACHINE_ENABLE` | switch | 開始洗衣 |  |
| `0x13` | `WASHING_MACHINE_REMAING_WASH_TIME` | sensor | 預估洗衣完成時間 | 僅在 `0x50=2` 動作中時，正常分鐘值顯示為目前時間 + 分鐘數的 `HH:MM`；預約中/待機/終了顯示 unknown。 |
| `0x14` | `WASHING_MACHINE_TIMER` | sensor | 預約時間設定 |  |
| `0x19` | `WASHING_MACHINE_ERROR_CODE` | sensor | 異常代碼 |  |
| `0x50` | `WASHING_MACHINE_OPERATING_STATUS` | sensor | 運轉情報 |  |
| `0x54` | `WASHING_MACHINE_CURRENT_MODE` | sensor | 目前洗衣行程 |  |
| `0x55` | `WASHING_MACHINE_CURRENT_PROGRESS` | sensor | 洗衣行程設定 |  |
| `0x69` | `WASHING_MACHINE_WARM_WATER` | switch | 溫水設定 |  |
| `0x15` | `WASHING_MACHINE_TIMER_REMAINING_TIME_OLD` | sensor | 預約洗衣開始時間 | 僅在 `0x50=3/4` 預約中時，正常分鐘值顯示為目前時間 + 分鐘數的 `HH:MM`；運轉中/待機/終了顯示 unknown。 |
| `0x60` | `WASHING_MACHINE_60` | sensor | 時間調整 |  |
| `0x61` | `WASHING_MACHINE_61, WASHING_MACHINE_POSTPONE_DRYING_TIME` | sensor | 延後晾衣設定 |  |
| `0x64` | `WASHING_MACHINE_PROGRESS_NEW` | sensor | 行程設定 |  |


### HDH `DeviceGetInfo` supplemental list

這些是 metadata 沒列、但已確認可 targeted `DeviceGetInfo` 讀取的 key：

| Key | 對應常數名稱 | HA 平台 | 顯示名稱 | 顯示/換算 |
|---|---|---|---|---|
| `0x58` | `WASHING_MACHINE_TIMER_REMAINING_TIME` | sensor | 預約洗衣完成時間 | 僅在 `0x50=3/4` 預約中時，正常分鐘值顯示為目前時間 + 分鐘數的 `HH:MM`；運轉中/待機/終了或 `>=60000` sentinel 顯示 unknown。 |
| `0x1E` | `WASHING_MACHINE_ENERGY` | sensor | 用電量 | sensor 顯示層 `raw × 0.1`，單位 kWh；小於 1 回 None。 |
| `0x74` | `WASHING_MACHINE_REMOTE_CONTROL` | sensor | 遠端遙控 | 本地 enum override：`0=關閉`, `1=開啟`。 |
| `0x76` | `WASHING_MACHINE_DETERGENT_AMOUNT` | sensor | 洗劑投入設定 |  |
| `0x77` | `WASHING_MACHINE_SOFTENER_AMOUNT` | sensor | 柔軟劑投入設定 |  |


### HDH supplemental display list

這是 UI/文件上的 supplemental display list，包含 `DeviceGetInfo` supplemental 與非 `DeviceGetInfo` 來源的補充 key。注意：`0xA2/0xA3/0xB0` 不會被送去 `DeviceGetInfo`。

| Key | 對應常數名稱 | HA 平台 | 顯示名稱 | 顯示/換算 |
|---|---|---|---|---|
| `0x58` | `WASHING_MACHINE_TIMER_REMAINING_TIME` | sensor | 預約洗衣完成時間 | 僅在 `0x50=3/4` 預約中時，正常分鐘值顯示為目前時間 + 分鐘數的 `HH:MM`；運轉中/待機/終了或 `>=60000` sentinel 顯示 unknown。 |
| `0x1E` | `WASHING_MACHINE_ENERGY` | sensor | 用電量 | sensor 顯示層 `raw × 0.1`，單位 kWh；小於 1 回 None。 |
| `0x74` | `WASHING_MACHINE_REMOTE_CONTROL` | sensor | 遠端遙控 | 本地 enum override：`0=關閉`, `1=開啟`。 |
| `0x76` | `WASHING_MACHINE_DETERGENT_AMOUNT` | sensor | 洗劑投入設定 |  |
| `0x77` | `WASHING_MACHINE_SOFTENER_AMOUNT` | sensor | 柔軟劑投入設定 |  |
| `0xA2` | `ENTITY_WATER_USED` | sensor | 當月用水量 | UserGetInfo raw 直接顯示，單位 L。 |
| `0xA3` | `ENTITY_WASH_TIMES` | sensor | 當月洗衣次數 | UserGetInfo raw 直接顯示。 |
| `0xB0` | `ENTITY_UPDATE` | binary_sensor | 版本更新 | UpdateCheck boolean，binary_sensor 顯示 on/off。 |


### HDH model-specific selects

這些是 HDH 遠端 `CommandList` 有宣告的設定 key；新版只對 `ModelType=HDH` 建立 select，不套用到尚未確認的 DDH/DW/MDH。

| Key | 常數名稱 | Select 名稱 | 備註 |
|---|---|---|---|
| `0x14` | `WASHING_MACHINE_TIMER` | 預約時間設定 | HDH CommandList-backed writable setting。 |
| `0x60` | `WASHING_MACHINE_60` | 時間調整 | HDH CommandList-backed writable setting。 |
| `0x61` | `WASHING_MACHINE_POSTPONE_DRYING_TIME` | 延後晾衣設定 | 正式設定 key；不要用 `0x56` 代表設定。 |
| `0x64` | `WASHING_MACHINE_PROGRESS_NEW` | 行程設定 | HDH CommandList-backed course setting。 |

舊版 HA entity registry 若殘留 restored/unavailable selects，應刪除：`0x02` 行程、`0x14` 舊預約時間設定、`0x56` 舊延後晾衣設定。新版不再用 `0x02` 或 `0x56` 作為 washer select。


### HDH 名稱與值 override

| 類型 | Key | Override |
|---|---|---|
| 名稱 | `0x13` | 預估洗衣完成時間 |
| 名稱 | `0x58` | 預約洗衣完成時間 |
| 名稱 | `0x15` | 預約洗衣開始時間 |
| 名稱 | `0x54` | 目前洗衣行程 |
| 名稱 | `0x55` | 洗衣行程設定 |
| 名稱 | `0x74` | 遠端遙控 |
| 值 | `0x74` | `0=關閉`, `1=開啟` |

## 顯示值是否 raw / 有無換算

| Key / 類型 | 來源 | 顯示處理 |
|---|---|---|
| `SensorDeviceClass.ENERGY`，例如 washer `0x1E` | `DeviceGetInfo` | 既有即時/累積 energy sensor 顯示名稱為「累積用電量」；`sensor.py` 顯示層會做 `raw × 0.1`，單位 kWh；小於 1 回 None。 |
| `0x13` 預估洗衣完成時間 | `DeviceGetInfo` main | 僅在 `0x50=2` 動作中時顯示目前時間 + 分鐘數的 `HH:MM`；預約中/待機/終了或 `>=60000` 顯示 unknown。 |
| `0x15` 預約洗衣開始時間 | `DeviceGetInfo` main | 僅在 `0x50=3/4` 預約中時顯示目前時間 + 分鐘數的 `HH:MM`；運轉中/待機/終了或 `>=60000` 顯示 unknown。 |
| `0x58` 預約洗衣完成時間 | `DeviceGetInfo` supplemental | 僅在 `0x50=3/4` 預約中時顯示目前時間 + 分鐘數的 `HH:MM`；運轉中/待機/終了或 `>=60000` sentinel 顯示 unknown。 |
| `0x74` 遠端遙控 | `DeviceGetInfo` supplemental | 本地 enum override：`0=關閉`, `1=開啟`。 |
| `0xA2` 當月用水量 | `UserGetInfo` / `WM_WaterUsed_Total` | raw 直接顯示，單位 L；日/月歷史 bucket 匯入 recorder external statistics。 |
| `0xA3` 當月洗衣次數 | `UserGetInfo` / `WM_WashTime_Total` | raw 直接顯示；日/月歷史 bucket 匯入 recorder external statistics。 |
| `UserGetInfo` 圖表用電量 | `UserGetInfo` / `Power` | `Total_kwh` 已是 kWh，不做 `×0.1`；日/月 bucket 匯入 recorder external statistics，交給官方 `statistics-graph` 顯示。 |
| `0xB0` 版本更新 | `UpdateCheck` | bool，binary_sensor 顯示 on/off。 |
| Fridge temperature 類 | `DeviceGetInfo` | `sensor.py` 對 fridge 有額外數值修正：大於 60000/30000/200 時分別做 offset。 |
| PM2.5 `65535` | `DeviceGetInfo` | `_workaround_info()` 會把 climate/dehumidifier PM2.5 的 `65535` 改為 `0`。 |

## UserGetInfo external statistics / statistics-graph

`UserGetInfo` 的日/月 bucket 值匯入 Home Assistant recorder external statistics；真正的視覺化交給官方 `statistics-graph` dashboard card。

不要用 attributes 或 custom SVG camera 當圖表資料來源。`statistics-graph` card 讀的是 Home Assistant recorder statistics；Panasonic 的 `UserGetInfo` bucket 值應匯入 external statistics，再由官方卡片顯示。前端卡片也要求 HA `history` integration 已載入；若測試用 HA shadow 沒有 `default_config:`，需在 `configuration.yaml` 明確加 `history:`，否則卡片只會顯示「歷史整合已關閉」。

Dashboard 注意事項：

- 卡片用 `stat_types: [state]` 顯示 Panasonic API bucket 值；不要用 `change`，否則 tooltip/legend 會在名稱後面顯示「（變更）」。
- 不同單位不要放同一張 `statistics-graph`；例如洗衣機用水量是 L、洗衣次數是「次」，必須拆成兩張卡。
- 對 external statistic id，不要在 `statistics-graph` 本身放 `title`；HA 會自動產生 History 連結，但 History 頁只懂 state entity，不懂 external statistic id，會顯示看不懂的 id 並在上一筆/下一筆時出現「找不到狀態歷史」。標題請用獨立 `heading` card。
- Integration 不應安裝後自動修改使用者 Lovelace storage；專案提供根目錄 `dashboard_template.yaml` 作為可手動貼上/匯入的範本。
- 範本採 `type: sections`、`max_columns: 2`；每種數據以兩個相鄰 section 排列，30 日（日統計）在左、12 個月（月統計）在右，避免用巢狀 `grid columns: 2` 把卡片縮成半寬。

External statistic id 分日/月兩種粒度，避免日資料和月資料在同一 timestamp 互相覆寫：

| Metric | UserGetInfo 欄位 | Day statistic id suffix | Month statistic id suffix | 單位 |
|---|---|---|---|---|
| 用電量 | `Power.kwh` | `{gwid}_energy_day` | `{gwid}_energy_month` | kWh |
| 用水量 | `Other.WM_WaterUsed` | `{gwid}_water_day` | `{gwid}_water_month` | L |
| 洗衣次數 | `Other.WM_WashTime` | `{gwid}_wash_count_day` | `{gwid}_wash_count_month` | 次 |

最小 view YAML 範例（完整範本見 [`../dashboard_template.yaml`](../dashboard_template.yaml)）：

```yaml
title: Panasonic 統計圖表
path: panasonic-statistics
type: sections
max_columns: 2
sections:
  - type: grid
    cards:
      - type: heading
        heading_style: title
        heading: 用電量 - 近 30 日（日統計）
      - type: statistics-graph
        chart_type: bar
        period: day
        days_to_show: 30
        stat_types:
          - state
        entities:
          - entity: panasonic_ems2:<gwid>_energy_day
            name: 客廳空調

  - type: grid
    cards:
      - type: heading
        heading_style: title
        heading: 用電量 - 近 12 個月（月統計）
      - type: statistics-graph
        chart_type: bar
        period: month
        days_to_show: 365
        stat_types:
          - state
        entities:
          - entity: panasonic_ems2:<gwid>_energy_month
            name: 客廳空調
```

## Weight plate / `PlateGetMode` 專用 key

`DEVICE_TYPE_WEIGHT_PLATE` 在 `get_devices_with_info()` 裡不走一般 `DeviceGetInfo` main flow，而是呼叫 `PlateGetMode` 後把以下欄位補進 status：

| Key | 常數名稱 | 來源欄位 |
|---|---|---|
| `0x80` | `WEIGHT_PLATE_FOOD_NAME` | `Name` |
| `0x81` | `WEIGHT_PLATE_MANAGEMENT_MODE` | `ManagementMode` |
| `0x82` | `WEIGHT_PLATE_MANAGEMENT_VALUE` | `ManagementValue` |
| `0x83` | `WEIGHT_PLATE_AMOUNT_MAX` | `AmountMax` |
| `0x84` | `WEIGHT_PLATE_BUY_DATE` | `BuyDate` timestamp → local datetime |
| `0x85` | `WEIGHT_PLATE_DUE_DATE` | `DueDate` timestamp → local datetime |
| `0x8A` | `WEIGHT_PLATE_COMMUNICATION_MODE` | `CommunicationMode` |
| `0x8B` | `WEIGHT_PLATE_COMMUNICATION_TIME` | `CommunicationTime` |
| `0x8C` | `WEIGHT_PLATE_TOTAL_WEIGHT` | `TotalWeight` |
| `0x8D` | `WEIGHT_PLATE_RESTORE_WEIGHT` | `RestoreWeight` |
| `0x8E` | `WEIGHT_PLATE_LOW_BATTERY` | `LowBattery` |

## 不確定 / 暫不啟用 HDH keys

以下 key 目前不是 HDH 遠端 `CommandList` 主包，語意或穩定性尚未確認，因此應保持註解，不要常態讀取：

| Key | 常數名稱 | 備註 |
|---|---|---|
| `0x03` | `WASHING_MACHINE_OPERATING_STATUS_OLD` | 舊式狀態欄位，與 `0x50` 關係未確認。 |
| `0x56` | `WASHING_MACHINE_POSTPONE_DRYING` | 延後晾衣狀態/設定語意未確認。 |
| `0x52` | `WASHING_MACHINE_52` | 未知欄位。 |
| `0x53` | `WASHING_MACHINE_53` | 未知欄位。 |
| `0x57` | `WASHING_MACHINE_57` | 未知欄位。 |
| `0x66` | `WASHING_MACHINE_66` | 未知欄位。 |
| `0x67` | `WASHING_MACHINE_67` | 未知欄位。 |

## 快速結論

- `DeviceGetInfo` 是大部分即時狀態 key 的來源，且分 main / supplemental。
- `CommandList` 不是 status 值來源；它是 metadata 來源，用來判斷哪些 key 是官方遠端宣告支援，並提供 `CommandName` / enum/range。
- `UserGetInfo` integration 會用 `Other` 補 washer 的 `0xA2/0xA3` 當月值，並低頻抓 `Power` / `Other` 把日/月 bucket 匯入 recorder external statistics，供官方 `statistics-graph` dashboard card 顯示；不要建立 `0xA*_today/current_month/...` sensor 或 SVG camera 圖表 entity。
- `UserGetInfo` 實測接受 `unit=day` 與 `unit=month`；`unit=mon/year` 會回 `傳入的unit錯誤`。當日/當月/近 30 日用 `day`，當年/近 1 年用 `month`。
- `UpdateCheck` 補 `0xB0/0xB1`，不是 `DeviceGetInfo`。
- `PlateGetMode` 是重量盤專用來源。
- `UserGetDeviceStatus` 只當 quick gate，不等於 HA 完整 entity list。
