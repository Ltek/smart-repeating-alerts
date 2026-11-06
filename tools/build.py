#!/usr/bin/env python3
"""Build smart-alerts-ltek.yaml from Repeating Alerts (_base-repeating-alerts.yaml) plus the Smart Alerts additions.

Repeating Alerts' code paths are kept as they are (they carry many field fixes); the additions are applied as
checked text edits, so every edit fails loudly if the base changes under it.

    python3 tools/build.py            # writes smart-alerts-ltek.yaml
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "_base-repeating-alerts.yaml"
OUT = ROOT / "smart-alerts-ltek.yaml"
VERSION = (ROOT / "VERSION").read_text().strip()


def must(s: str, old: str, new: str, count: int = 1) -> str:
    n = s.count(old)
    if n != count:
        sys.exit(f"build: expected {count} x {old[:70]!r}, found {n}")
    return s.replace(old, new)


s = BASE.read_text()

# ── header ───────────────────────────────────────────────────────────────────────────────────────────────────────────
head_end = s.index("    Author: LTek")
s = (
    f"""blueprint:
  name: ⚠️ Smart Alerts by LTek
  description: |

    **Repeating, actionable alerts for doors, windows, leaks, cameras and more**

    🚀 Version {VERSION}

    Smart Alerts is Repeating Alert Notifications (2026.07.30.39) plus camera snapshots, more delivery options and a
    test mode. Every Repeating Alerts input keeps its name, so an existing Repeating Alerts automation switches by
    changing only its blueprint path.

    New in Smart Alerts:
    - 📸 Camera snapshot attached to every notification (snapshot delay, file path, optional archive copy)
    - 🔗 Buttons can open a URL or a dashboard (URI) instead of running an action
    - 📮 Extra notify services (e.g. notify.family) next to the mobile devices, and an Android notification group
    - 🤖 Android priority, vibration pattern, LED color and the alarm stream
    - ⏳ Cooldown: ignore a new alert this soon after the last one
    - 🧪 Test mode: send only to test devices, or only to the Home Assistant notification bell
    - ✏️ `action:` syntax everywhere

"""
    + s[head_end:]
)
s = must(
    s,
    "  source_url: https://gist.github.com/Ltek/0d88ed720f635a7579849aac93b9ff93",
    "  source_url: https://github.com/Ltek/smart-alerts/blob/main/smart-alerts-ltek.yaml",
)
s = re.sub(r"Repeating Alert - ([A-Z])", r"Smart Alert - \1", s)  # debug notification titles

# ── new inputs ───────────────────────────────────────────────────────────────────────────────────────────────────────
s = must(
    s,
    "              custom_value: false\n              multiple: false\n              sort: false\n\n        notification_color:",
    "              custom_value: true\n              multiple: false\n              sort: false\n\n        notification_color:",
)
URI_INPUT = """        action_button_{n}_uri:
          name: "Button {n} URI (optional)"
          description: >
            Open this URL, dashboard path (e.g. /dashboard-home/cameras) or app view (e.g. entityId:camera.patio)
            instead of running Button {n} Action.
          default: ""
          selector:
            text: {{}}

"""
for n in (1, 2, 3):
    anchor = f"        action_button_{n}_action:\n"
    s = must(s, anchor, URI_INPUT.format(n=n) + anchor)

NEW_SECTIONS = """    # ── SECTION: Camera Snapshot (from Smart Camera Notifications) ─────────────
    section_camera:
      name: "Camera Snapshot"
      icon: mdi:cctv
      collapsed: true
      input:
        camera:
          name: "Camera"
          description: Take a snapshot from this camera and attach it to every notification. Leave empty for none.
          default: ""
          selector:
            entity:
              domain: camera
        snapshot_delay:
          name: "Snapshot Delay"
          description: Seconds to wait after the trigger before the snapshot.
          default: 0
          selector:
            number:
              min: 0
              max: 30
              step: 0.5
              unit_of_measurement: s
        snapshot_file_path:
          name: "Snapshot File Path"
          description: >
            Where the snapshot is saved. Under /media it is sent as /media/local/..., under /config/www as /local/...
          default: "/media/snapshots/{{ camera_object_id }}_last.jpg"
          selector:
            text: {}
        save_archive_file:
          name: "Save an Archive Copy"
          default: false
          selector:
            boolean: {}
        archive_file_path:
          name: "Archive File Path"
          default: "/media/snapshots/{{ camera_object_id }}/{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
          selector:
            text: {}

    # ── SECTION: More Delivery Options ───────────────────────────────────────────
    section_delivery:
      name: "More Delivery Options"
      icon: mdi:send-variant
      collapsed: true
      input:
        notify_services:
          name: "Extra Notify Services"
          description: Also send to these notify services (e.g. notify.family, notify.living_room_tv).
          default: []
          selector:
            select:
              options: []
              custom_value: true
              multiple: true
        notification_group:
          name: "Notification Group (Android)"
          description: Android groups notifications with the same group name.
          default: ""
          selector:
            text: {}
        cooldown_time:
          name: "Cooldown"
          description: Ignore a new alert this many seconds after the last one (0 = off). Useful for cameras.
          default: 0
          selector:
            number:
              min: 0
              max: 3600
              unit_of_measurement: s
        test_mode:
          name: "Test Mode"
          description: >
            Send only to the Test Devices below (and the Home Assistant notification bell), not to Devices to Notify
            or the extra notify services. Actions, buttons and repeats run as normal.
          default: false
          selector:
            boolean: {}
        test_notify_device:
          name: "Test Devices"
          default: []
          selector:
            device:
              integration: mobile_app
              multiple: true

"""
s = must(s, "    # ── SECTION: Android Options ──────────────────────────────────────────────\n",
         NEW_SECTIONS + "    # ── SECTION: Android Options ──────────────────────────────────────────────\n")

ANDROID_EXTRA = """        android_priority:
          name: "Priority (Android)"
          description: high delivers at once, even in Doze.
          default: default
          selector:
            select:
              options: [default, high]
        android_alarm_stream:
          name: "Use the Alarm Stream (Android)"
          description: Play the notification sound as an alarm, even when the phone is silent (channel alarm_stream).
          default: false
          selector:
            boolean: {}
        android_vibration_pattern:
          name: "Vibration Pattern (Android)"
          description: e.g. 100, 1000, 100, 1000 (only used when a new channel is created).
          default: ""
          selector:
            text: {}
        android_led_color:
          name: "LED Color (Android)"
          description: e.g. red or #FF0000 (only used when a new channel is created).
          default: ""
          selector:
            text: {}

"""
s = must(s, "    # ── SECTION: iOS Options", ANDROID_EXTRA + "    # ── SECTION: iOS Options")

# ── variables ────────────────────────────────────────────────────────────────────────────────────────────────────────
s = must(
    s,
    "  repeat_count: 0\n\ntriggers:",
    """  repeat_count: 0
  camera: !input camera
  camera_object_id: "{{ camera.split('.', 1)[1] if camera else '' }}"
  camera_name: "{{ state_attr(camera, 'friendly_name') if camera else '' }}"
  snapshot_delay: !input snapshot_delay
  save_archive_file: !input save_archive_file
  notify_services_extra: !input notify_services
  notification_group: !input notification_group
  cooldown_time: !input cooldown_time
  test_mode: !input test_mode
  test_notify_device: !input test_notify_device
  android_priority: !input android_priority
  android_alarm_stream: !input android_alarm_stream
  android_vibration_pattern: !input android_vibration_pattern
  android_led_color: !input android_led_color
  time: "{{ now().strftime('%I:%M %p') }}"

triggers:""",
)

# ── delivery list: test devices in test mode, plus extra services (main and restart-restore paths) ────────────────────
if s.count("{% for device_id in notify_device %}") != 2:
    sys.exit("build: expected 2 device loops")
s = s.replace("{% for device_id in notify_device %}", "{% for device_id in (test_notify_device if test_mode else notify_device) %}")


def _extra(m: re.Match) -> str:
    ind = m.group(1)
    return (
        f"{ind}{{% endfor %}}\n"
        f"{ind}{{% if not test_mode %}}\n"
        f"{ind}  {{% for svc in notify_services_extra %}}\n"
        f"{ind}    {{% set svc = svc | trim %}}\n"
        f"{ind}    {{% if svc %}}{{% set ns.services = ns.services + [svc if svc.startswith('notify.') else 'notify.' ~ svc] %}}{{% endif %}}\n"
        f"{ind}  {{% endfor %}}\n"
        f"{ind}{{% endif %}}\n"
        f"{ind}{{{{ ns.services | unique | list }}}}\n"
    )


s, n = re.subn(r"^( *)\{% endfor %\}\n\1\{\{ ns\.services \}\}\n", _extra, s, flags=re.M)
if n != 2:
    sys.exit(f"build: expected 2 service lists, found {n}")
# test mode always mirrors to the notification bell
s = s.replace("value_template: '{{ enable_webui_normal_notifications }}'",
              "value_template: '{{ enable_webui_normal_notifications or test_mode }}'")

# ── cooldown + snapshot, right after the trigger check ──────────────────────────────────────────────────────────────
TRIGGER_CHECK = """  - condition: template
    value_template: >
      {{ trigger.id == "ha_restart" or
         (trigger.idx is defined and
          trigger.idx | int(-1) < (alert_trigger_count + clear_trigger_count + resolution_trigger_count)) }}
"""
SNAP = TRIGGER_CHECK + """
  # ── Smart Alerts: cooldown, then the camera snapshot ─────────────────────────
  - variables:
      is_alert_trigger: "{{ trigger.idx is defined and trigger.idx | int(-1) < alert_trigger_count }}"
      snapshot_create_file_path: !input snapshot_file_path
      archive_create_file_path: !input archive_file_path
      snapshot_url: >
        {% if camera %}{{ snapshot_create_file_path | replace('/config/www', '/local') | replace('/media', '/media/local', 1) }}{% endif %}
  - condition: template
    value_template: >
      {{ not is_alert_trigger or cooldown_time | int(0) <= 0 or not this.attributes.last_triggered or
         (now() - this.attributes.last_triggered).total_seconds() > cooldown_time | int(0) }}
  - if:
      - condition: template
        value_template: "{{ is_alert_trigger and camera != '' }}"
    then:
      - delay:
          seconds: "{{ snapshot_delay | float(0) }}"
      - action: camera.snapshot
        target:
          entity_id: "{{ camera }}"
        data:
          filename: "{{ snapshot_create_file_path }}"
        continue_on_error: true
      - if:
          - condition: template
            value_template: "{{ save_archive_file }}"
        then:
          - action: camera.snapshot
            target:
              entity_id: "{{ camera }}"
            data:
              filename: "{{ archive_create_file_path }}"
            continue_on_error: true
"""
s = must(s, TRIGGER_CHECK, SNAP)

# ── extra data on every real notification (not on clear_notification) ──────────────────────────────────────────────
lines = s.split("\n")
out: list[str] = []
added = 0
for i, line in enumerate(lines):
    out.append(line)
    if line.strip() == "tag: '{{ notification_tag }}'":
        back = "\n".join(lines[max(0, i - 6): i])
        if "clear_notification" in back:
            continue
        ind = line[: len(line) - len(line.lstrip())]
        out += [
            f"{ind}image: \"{{{{ snapshot_url if snapshot_url | default('') else None }}}}\"",
            f"{ind}group: \"{{{{ notification_group if notification_group else None }}}}\"",
            f"{ind}priority: \"{{{{ 'high' if android_priority == 'high' else None }}}}\"",
            f"{ind}ttl: \"{{{{ 0 if android_priority == 'high' else None }}}}\"",
            f"{ind}vibrationPattern: \"{{{{ android_vibration_pattern if android_vibration_pattern else None }}}}\"",
            f"{ind}ledColor: \"{{{{ android_led_color if android_led_color else None }}}}\"",
        ]
        added += 1
if added != 7:
    sys.exit(f"build: only {added} notification sends found")
s = "\n".join(out)
# alarm stream wins over the channel
s = s.replace("channel: '{{ android_channel }}'", "channel: \"{{ 'alarm_stream' if android_alarm_stream else android_channel }}\"")

# ── URI buttons: the button opens the URI instead of firing an event ────────────────────────────────────────────────
for n in (1, 2, 3):
    old = (f"{{% set actions = actions + [{{'action': 'BTN{n}_' ~ context.id, 'title': action_button_{n}_label}}] %}}")
    new = (f"{{% set uri = action_button_{n}_uri | default('') %}}"
           f"{{% set actions = actions + [{{'action': 'URI', 'title': action_button_{n}_label, 'uri': uri}} if uri"
           f" else {{'action': 'BTN{n}_' ~ context.id, 'title': action_button_{n}_label}}] %}}")
    s = must(s, old, new, count=2)
s = must(s, "  action_button_3_label: !input action_button_3_label\n",
         "  action_button_3_label: !input action_button_3_label\n"
         "  action_button_1_uri: !input action_button_1_uri\n"
         "  action_button_2_uri: !input action_button_2_uri\n"
         "  action_button_3_uri: !input action_button_3_uri\n")

# ── modern syntax ────────────────────────────────────────────────────────────────────────────────────────────────────
s = re.sub(r"^(\s*-?\s*)service: ", r"\1action: ", s, flags=re.M)
s = re.sub(r"^(\s*-?\s*)platform: ", r"\1trigger: ", s, flags=re.M)
s = must(s, "\naction:\n  - variables:\n", "\nactions:\n  - variables:\n")

OUT.write_text(s)
print(f"wrote {OUT.name}: {len(s.splitlines())} lines, {added} notification sends extended")
