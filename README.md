# ⚠️ Smart Alerts by LTek

A Home Assistant **automation blueprint** for repeating, actionable alerts: doors, windows, leaks, smoke and CO,
temperatures, cameras and anything else with a trigger.

It is [Repeating Alert Notifications](https://community.home-assistant.io/t/repeating-alert-notifications/888294)
with the camera snapshots of Smart Camera Notifications and more delivery options. Every Repeating Alerts input keeps
its name, so an existing Repeating Alerts automation switches by changing only its blueprint path to
`LTek/smart-alerts-ltek.yaml`.

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLtek%2Fsmart-alerts%2Fblob%2Fmain%2Fsmart-alerts-ltek.yaml)

## What it does

- **Any trigger** (state, numeric, template, event, device), optional conditions, a delay before the first alert.
- **Repeats** until cleared, with a maximum count, a final notification, and a *resolved* notification when a
  resolution trigger fires. Optional restart survival with a timer and a text helper.
- **Notification ID (tag)**: a new alert replaces the last one; clearing removes it from the phone.
- **Up to 3 buttons** plus Cancel. A button runs actions, or opens a URL or dashboard. Button timeout and a failsafe
  action when nobody answers.
- **Camera snapshot** attached to every notification, with a snapshot delay and an optional archive copy.
- **Delivery**: mobile devices, extra notify services, the Home Assistant notification bell, an Android group.
- **Android**: icon, color, channel, sticky, wake screen, priority, vibration pattern, LED color, the alarm stream.
  **iOS**: interruption level (critical), sound.
- **Cooldown** between alerts, and a **test mode** that sends only to test devices and the notification bell.

## Variables for titles and messages

`friendly_name`, `device_name`, `entity_area_name`, `trigger_entity_state`, `time_since_trigger`, `trigger_fired_at`,
`camera_name`, `time`, and any template.

## Building

`smart-alerts-ltek.yaml` is generated: `python3 tools/build.py` applies the Smart Alerts additions to
`_base-repeating-alerts.yaml` (Repeating Alerts 2026.07.30.39). Tests: `pytest tests` with
`pytest-homeassistant-custom-component` installed.

`tools/convert.py <automations.yaml> <dir>` converts Repeating Alerts and Smart Camera Notifications automations to
Smart Alerts, one file each, and lists what it mapped.

See [CHANGELOG.md](CHANGELOG.md).
