[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/choucheyu/panasonic_ems2?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/choucheyu/panasonic_ems2?style=for-the-badge)](LICENSE)

[繁體中文](README_zh-tw.md) | [English](README.md)

# Panasonic Smart IoT TW for Home Assistant (Taiwan Enhanced)

A Home Assistant custom integration for Panasonic IoT TW / Panasonic Smart Home appliances, focused on Taiwan Panasonic Smart Home new-model support, Traditional Chinese UI wording, and official statistics dashboard workflows.

This is a Taiwan-focused maintained fork of [`tsunglung/panasonic_ems2`](https://github.com/tsunglung/panasonic_ems2), which was originally based on [`osk2/panasonic_smart_app`](https://github.com/osk2/panasonic_smart_app). The original Apache-2.0 license is preserved.

## What is different in this fork / highlights

This fork keeps the original Panasonic cloud appliance integration goal, but adds fuller Home Assistant support for Taiwan Panasonic Smart Home / Panasonic IoT TW new models and real-world usage:

- **Taiwan new-model support**: practical fixes for incomplete Panasonic cloud model metadata, especially VX/UX/UJ/UK-style climates and HDH washers such as `NA-V160HDH`.
- **Climate support improvements**: VX-series supplemental cloud status reads, plus operating-mode, fan-speed, mildew-related controls/status, indoor humidity, voice, PM2.5, airflow, and range fallbacks when model metadata is incomplete.
- **HDH washer semantics**: CommandList-aligned main polling to avoid unstable large reads, with clearer display semantics for remote control, detergent/softener amounts, estimated/reservation times, and raw status values.
- **HDH washer setting selects**: `0x14` reservation time, `0x60` time adjustment, `0x61` delayed airing, and `0x64` course setting are exposed as HDH model-specific selects; legacy `0x56` stays a raw delayed-airing status, not a setting select.
- **Panasonic statistics charts**: `UserGetInfo` day/month buckets are imported into Home Assistant recorder external statistics so energy, washer water usage, and wash count can be displayed with the official `statistics-graph` card.
- **Dashboard template**: `dashboard_template.yaml` provides an optional Lovelace view template that users can import or paste manually. The integration does not silently mutate user dashboards.
- **Taiwan-focused UX**: switch raw-value handling fixes plus Traditional Chinese wording and Home Assistant UI text updates.

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

## Panasonic statistics dashboard

The integration imports Panasonic `UserGetInfo` day/month buckets into Home Assistant recorder external statistics for the official `statistics-graph` card. Installing the integration does **not** automatically change your Lovelace dashboard.

Use the repository-root `dashboard_template.yaml` as an optional Lovelace view template. Replace the placeholder statistic IDs with your device GWIDs, then paste/import it into your dashboard. The template groups the same metric on one row: 30-day/day statistics on the left and 12-month/month statistics on the right. Make sure Home Assistant loads both `recorder` and `history` integrations.

The template includes:

- Energy: 30 days / 12 months
- Washer water usage: 30 days / 12 months
- Washer wash count: 30 days / 12 months

Different units are split into different cards so wash count is not displayed as liters. The `statistics-graph` cards intentionally omit `title` to avoid linking external statistic IDs to state-history pages.

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
