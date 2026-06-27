[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/choucheyu/panasonic_ems2?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/choucheyu/panasonic_ems2?style=for-the-badge)](LICENSE)

[English](README.md) | [繁體中文](README_zh-tw.md)

# Panasonic Smart IoT TW for Home Assistant（台灣加強版）

這是給 Home Assistant 使用的 Panasonic IoT TW / Panasonic Smart Home 自訂整合，目標是補強台灣 Panasonic Smart Home 新型號、繁體中文顯示與統計圖表使用情境。

本專案是 [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2) 的台灣使用情境維護版；原專案則源自 [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app)。本 fork 保留原始 Apache-2.0 授權與來源標示。

## 這個 fork 的重點與差異

這個 fork 保留原本整合 Panasonic 雲端家電的目標，但針對台灣 Panasonic Smart Home / Panasonic IoT TW 的新型號與實際使用情境，補上更完整的 Home Assistant 支援：

- **台灣新型號補強**：針對 Panasonic cloud 回傳的 model metadata 實測補洞，尤其是 VX/UX/UJ/UK 類空調與 HDH 系列洗衣機（例如 `NA-V160HDH`）。
- **空調支援補強**：加入 VX 系列 supplemental cloud status 讀取；當 metadata 不完整時，補上運轉模式、風量、防霉相關控制/狀態、室內濕度、語音、PM2.5、風向/風量等實體與 range fallback。
- **HDH 洗衣機語意修正**：依官方 CommandList 調整主輪詢 key，避免不穩定的大包讀取；修正遠端遙控、洗劑/柔軟劑投入量、預估/預約時間與 raw 狀態的顯示語意。
- **HDH 洗衣機設定 select**：`0x14` 預約時間設定、`0x60` 時間調整、`0x61` 延後晾衣設定、`0x64` 行程設定會以 HDH model-specific select 建立；舊 `0x56` 僅保留為延後晾衣 raw 狀態，不當成設定 select。
- **Panasonic 統計圖表**：將 `UserGetInfo` 日/月統計匯入 Home Assistant recorder external statistics，讓用電量、洗衣機用水量、洗衣次數可用官方 `statistics-graph` 卡片顯示。
- **Dashboard 範本**：根目錄 `dashboard_template.yaml` 提供可手動匯入/貼上的 Lovelace view 範本；整合本身不會自動修改使用者 dashboard。
- **台灣使用體驗調整**：修正 switch raw value 轉換，並調整繁體中文與 Home Assistant UI 顯示文字。

> 實際可用功能仍取決於你的家電型號，以及 Panasonic 雲端 API 對該型號回傳的 command metadata。

## 目前目標支援類別

本整合目前針對 Panasonic Smart Home / Panasonic IoT TW 雲端 API 暴露的裝置，包含：

- 空調
- 洗衣機
- 冰箱
- 除濕機
- 全熱交換器 / 換氣設備
- 重量感知板

Panasonic 家電型號很多，不同型號的 command metadata 可能不同。如果你的裝置缺少實體、功能不完整或行為異常，請在本 repo 開 issue 並提供型號與 command 資訊。

## 安裝

### HACS custom repository

1. 打開 Home Assistant 的 HACS。
2. 進入 **Integrations**。
3. 點右上角選單，選擇 **Custom repositories**。
4. 加入這個 repository：

   ```text
   https://github.com/choucheyu/panasonic_ems2
   ```

5. Category 選 **Integration**。
6. 安裝 **Panasonic Smart IoT TW**。
7. 重新啟動 Home Assistant。

### 手動安裝

將本 repo 的這個資料夾：

```text
custom_components/panasonic_ems2
```

複製到 Home Assistant config 目錄底下：

```text
<config>/custom_components/panasonic_ems2
```

然後重新啟動 Home Assistant。

## 設定

請使用 Home Assistant 的 config flow：

1. 前往 **設定 > 裝置與服務 > 新增整合**。
2. 搜尋 **Panasonic Smart IoT TW**。
3. 輸入 Panasonic Smart Home / Panasonic IoT TW 帳號密碼。
4. 完成設定，等待 Home Assistant 載入家電。

## Panasonic 統計圖表

本整合會把 Panasonic `UserGetInfo` 的日/月統計匯入 Home Assistant recorder external statistics，供官方 `statistics-graph` card 使用；安裝整合本身不會自動修改你的 Lovelace dashboard。

專案根目錄提供 `dashboard_template.yaml`，可手動貼到 Lovelace view 或依你的 GWID 調整後匯入。範本採用每種數據一組左右排列：左側為近 30 日（日統計），右側為近 12 個月（月統計）。使用前請確認 HA 已載入 `recorder` 與 `history` integration。

範本包含：

- 用電量：近 30 日 / 近 12 個月
- 洗衣機用水量：近 30 日 / 近 12 個月
- 洗衣機洗衣次數：近 30 日 / 近 12 個月

不同單位會拆成不同卡片，避免洗衣次數被顯示成 L；`statistics-graph` 本身不放 `title`，避免 History 頁誤把 external statistic id 當成 state entity。

## 協助新增或修正裝置支援

如果你的家電沒有出現、實體不完整，或控制行為異常，請先收集一份已遮蔽個資的 support bundle。單靠 command metadata 通常不足以安全新增實體或控制；唯讀 live snapshot 可以幫助判斷型號特定狀態值、補充 `DeviceGetInfo` key、統計資料支援與更新資訊。

1. 安裝 Python 3。
2. 下載本 repo 的輔助腳本：

   ```text
   https://github.com/choucheyu/panasonic_ems2/raw/master/scripts/panasonic_ems2.py
   ```

3. 在終端機執行：

   ```bash
   pip install requests
   python panasonic_ems2.py
   ```

4. 腳本會產生一份帶時間戳記且預設遮蔽的 support bundle：

   ```text
   panasonic_ems2_support_bundle_<timestamp>.json
   ```

   同時也會保留相容用的舊檔 `panasonic_devices.json` 與 `panasonic_commands.json`。

bundle 內容包含：

- `UserGetRegisteredGwList2` 回傳的 `GwList` 與 `CommandList`。
- 唯讀 `UserGetDeviceStatus` snapshot。
- 針對 CommandList 內 command 的唯讀 `DeviceGetInfo` snapshot。
- 用於統計 / 更新分析的 `UserGetInfo` 與 `S3/UpdateCheck` snapshot。
- 一份簡短觀察模板，用來補充官方 App 狀態、實體裝置狀態，以及 metadata 無法推論 command 語意時的 before/after 行為。

預設會遮蔽 auth、token、GWID、暱稱與裝置名稱；分享前仍請自行檢查 JSON。只有在本機私下除錯時才建議明確輸出 raw 檔：

```bash
python panasonic_ems2.py --raw-output
```

補充 command probe 會增加唯讀 API 呼叫量，因此必須明確 opt-in：

```bash
python panasonic_ems2.py --probe-supplemental
```

## 支持開發 / Buy Me A Coffee

如果這個台灣使用情境維護版對你的 Home Assistant 有幫助，可以掃描下方 QR code 支持後續維護。

<p align="center">
  <img src="assets/buy-me-a-coffee-qr.jpg" alt="Buy Me A Coffee QR code" width="220">
</p>

## 來源標示

本專案基於：

- [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2)
- [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app)

感謝原作者與貢獻者。本 fork 會以台灣 Home Assistant 使用情境與額外機型支援為主，獨立維護。
