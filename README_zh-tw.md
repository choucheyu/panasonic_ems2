[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/choucheyu/panasonic_ems2?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/choucheyu/panasonic_ems2?style=for-the-badge)](LICENSE)

[English](README.md) | [繁體中文](README_zh-tw.md)

# Panasonic Smart IoT TW for Home Assistant

這是給 Home Assistant 使用的 Panasonic IoT TW / Panasonic Smart Home 自訂整合。

本專案是 [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2) 的台灣使用情境維護版；原專案則源自 [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app)。本 fork 保留原始 Apache-2.0 授權與來源標示。

## 這個 fork 有哪些不同

這個 fork 保留原本整合 Panasonic 雲端家電的目標，但加入了針對台灣 Panasonic Smart Home 使用情境實測後的修正與補強：

- 補強 VX 系列空調支援與 supplemental cloud status 讀取。
- 當 Panasonic cloud 回傳的機型 metadata 不完整時，補上空調運轉模式與風量選項的 range fallback。
- 依裝置/cloud metadata 支援狀況，補上防霉相關控制/狀態、室內濕度、語音、PM2.5、風量等實體。
- 修正 switch entity 的 raw value 轉換。
- 調整繁體中文與 Home Assistant UI 顯示文字。

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

## 協助新增或修正裝置支援

如果你的家電沒有出現、實體不完整，或控制行為異常，請先收集該裝置的型號與 command metadata。

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

4. 腳本會產生 device / command JSON 檔。請在本 repo 開 issue，附上相關型號與 command 資訊。分享前請先移除 token、帳號或個人資料。

## 來源標示

本專案基於：

- [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2)
- [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app)

感謝原作者與貢獻者。本 fork 會以台灣 Home Assistant 使用情境與額外機型支援為主，獨立維護。
