# Changelog

Build numbers continue from Repeating Alert Notifications (last build 2026.07.30.39). Builds .1 to .3 below were
made locally before the numbering was settled and were never published; .42 is the first published build.

## v2026.11.06.43 — 2026-11-06

- FIXED: the camera variables (`camera_name`, …) were defined after `android_channel`, so a channel such as
  `{{ camera_name }} Snapshot` came out as ` Snapshot`. They are now defined first.

## v2026.11.06.42 — 2026-11-06

First published build of **Smart Repeating Alerts (Ltek)**, replacing Repeating Alert Notifications (Ltek) and Smart
Camera Notifications. Everything in .1 to .3 below: camera snapshots, URI buttons, extra notify services and Android
group, Android priority / vibration / LED / alarm stream, cooldown, test mode, `action:` syntax, and *Alerts per
Entity* (one alert per triggering entity).

## v2026.11.06.3 — 2026-11-06

- **Alerts per Entity** (Alert Trigger section). *One alert per triggering entity* gives each entity its own alert,
  buttons and repeats when the trigger covers a label or several entities: the tag is the Notification ID plus the
  entity, and a clear, a resolution or a new trigger for one entity stops only that entity's alert. Before, a
  second window opening (or any window closing) replaced or cleared the first window's alert. Restart Persistence is
  off in this mode. *One alert at a time* (the default) is unchanged.

## v2026.11.06.2 — 2026-11-06

- Renamed to **Smart Repeating Alerts (Ltek)**: file `smart-repeating-alerts-ltek.yaml`, repo
  `Ltek/smart-repeating-alerts`. No other changes.

## v2026.11.06.1 — 2026-11-06

First version: Repeating Alert Notifications 2026.07.30.39 plus
- camera snapshot on every notification (from Smart Camera Notifications), with archive copy;
- buttons that open a URI;
- extra notify services, Android notification group;
- Android priority, vibration pattern, LED color and the alarm stream (inputs some Repeating Alerts automations
  still set, which did nothing there);
- cooldown between alerts;
- test mode;
- `action:` and `trigger:` syntax throughout.
