[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/choucheyu/panasonic_ems2?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/choucheyu/panasonic_ems2?style=for-the-badge)](LICENSE)

[繁體中文](README_zh-tw.md) | [English](README.md)

# Panasonic Smart IoT TW for Home Assistant

A Home Assistant custom integration for Panasonic IoT TW / Panasonic Smart Home appliances.

This is a Taiwan-focused maintained fork of [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2), which was originally based on [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app). The original Apache-2.0 license is preserved.

## What is different in this fork

This fork keeps the original integration goal, but carries additional fixes and device support validated against Taiwan Panasonic Smart Home usage:

- Additional VX-series climate support and supplemental cloud status reads.
- Range fallback for climate operating mode and fan-speed options when model metadata is incomplete.
- Additional climate entities such as mildew-related controls/status, indoor humidity, voice, PM2.5, and fan-speed options where supported by the device/cloud metadata.
- Raw-value handling fixes for switch entities.
- Traditional Chinese wording and Home Assistant UI text updates.

> Device capability still depends on the exact appliance model and the command metadata returned by Panasonic's cloud API.

## Supported appliance categories

The integration currently targets Panasonic Smart Home / Panasonic IoT TW devices exposed by the cloud API, including:

- Climate / air conditioner
- Washing machine
- Fridge
- Dehumidifier
- ERV / ventilator
- Weight plate

Some models expose incomplete or model-specific command metadata. Please open an issue in this repository with model and command information when a device or entity is missing or behaves incorrectly.

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Go to **Integrations**.
3. Open the menu in the upper-right corner and choose **Custom repositories**.
4. Add this repository:

   ```text
   https://github.com/choucheyu/panasonic_ems2
   ```

5. Category: **Integration**.
6. Install **Panasonic Smart IoT TW**.
7. Restart Home Assistant.

### Manual installation

Copy the following folder from this repository:

```text
custom_components/panasonic_ems2
```

into your Home Assistant config folder:

```text
<config>/custom_components/panasonic_ems2
```

Then restart Home Assistant.

## Configuration

Use Home Assistant's config flow:

1. Go to **Settings > Devices & services > Add integration**.
2. Search for **Panasonic Smart IoT TW**.
3. Enter your Panasonic Smart Home / Panasonic IoT TW account credentials.
4. Finish setup and let Home Assistant discover your appliances.

## Help add or fix device support

If your appliance is missing, has incomplete entities, or behaves incorrectly, please collect the device model and command metadata.

1. Install Python 3.
2. Download the helper script from this repository:

   ```text
   https://github.com/choucheyu/panasonic_ems2/raw/master/scripts/panasonic_ems2.py
   ```

3. Run it from a terminal:

   ```bash
   pip install requests
   python panasonic_ems2.py
   ```

4. The script generates device/command JSON files. Open an issue in this repository and attach the relevant model and command information. Remove account tokens or personal information before sharing.

## Attribution

This project is based on:

- [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2)
- [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app)

Thanks to the original authors and contributors. This fork is maintained separately for Taiwan-focused Home Assistant usage and additional model support.
