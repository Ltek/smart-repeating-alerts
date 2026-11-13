#!/usr/bin/env python3
"""Build smart-repeating-alerts-ltek.yaml from Repeating Alerts (_base-repeating-alerts.yaml) plus the Smart Repeating Alerts additions.

Repeating Alerts' code paths are kept as they are (they carry many field fixes); the additions are applied as
checked text edits, so every edit fails loudly if the base changes under it.

    python3 tools/build.py            # writes smart-repeating-alerts-ltek.yaml
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "_base-repeating-alerts.yaml"
OUT = ROOT / "smart-repeating-alerts-ltek.yaml"
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
  name: ⚠️ Smart Repeating Alerts (Ltek)
  description: |

    **Repeating, actionable alerts for doors, windows, leaks, cameras and more**

    🚀 Version {VERSION}

    Smart Repeating Alerts is Repeating Alert Notifications (2026.07.30.39) plus camera snapshots, more delivery options and a
    test mode. Every Repeating Alerts input keeps its name, so an existing Repeating Alerts automation switches by
    changing only its blueprint path.

    New in Smart Repeating Alerts:
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
    "  source_url: https://github.com/Ltek/smart-repeating-alerts/blob/main/smart-repeating-alerts-ltek.yaml",
)
s = re.sub(r"Repeating Alert - ([A-Z])", r"Smart Repeating Alert - \1", s)  # debug notification titles

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
# A manual Run (Run actions / automation.trigger) has no trigger (trigger.platform is none): it counts as an alert, so
# the snapshot is taken and the notification sent, and it skips the cooldown.
MANUAL = "(trigger.platform is none and trigger.idx is not defined)"
SNAP = """  - variables:
      is_manual_run: "{{ %s }}"
  - condition: template
    value_template: >
      {{ trigger.id == "ha_restart" or is_manual_run or
         (trigger.idx is defined and
          trigger.idx | int(-1) < (alert_trigger_count + clear_trigger_count + resolution_trigger_count)) }}
""" % MANUAL + """
  # ── Smart Repeating Alerts: cooldown, then the camera snapshot ─────────────────────────
  - variables:
      is_alert_trigger: "{{ is_manual_run or (trigger.idx is defined and trigger.idx | int(-1) < alert_trigger_count) }}"
      snapshot_create_file_path: !input snapshot_file_path
      archive_create_file_path: !input archive_file_path
      snapshot_url: >
        {% if camera %}{{ snapshot_create_file_path | replace('/config/www', '/local') | replace('/media', '/media/local', 1) }}{% endif %}
  - condition: template
    value_template: >
      {{ is_manual_run or not is_alert_trigger or cooldown_time | int(0) <= 0 or not this.attributes.last_triggered or
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


# ── One alert per entity (parallel runs) ──────────────────────────────────────────────────────────────────────────────
# Restart mode keeps one alert per automation: with a label or several entities, a second entity's trigger (or any
# clear) cancels the first entity's alert. "One alert per triggering entity" runs each entity in its own run: a tag per
# entity, a clear / resolution / new trigger for an entity stops only that entity's run (a stop event the run listens
# for in every wait), and restart persistence is off (its helpers hold one alert).
s = must(s, "mode: restart\nmax_exceeded: silent\n", "mode: !input run_mode\nmax: 50\nmax_exceeded: silent\n")
s = must(
    s,
    "        duration_issue_state:\n          name: \"Time Delay before Alert is Sent\"",
    """        run_mode:
          name: "Alerts per Entity"
          description: >
            With a label or several entities, choose "One alert per triggering entity": each entity gets its own
            alert, buttons and repeats, and closing one entity clears only its alert (tag = Notification ID + the
            entity). "One alert at a time" is the Repeating Alerts behavior: a new trigger or any clear replaces the
            current alert. Restart Persistence works only with one alert at a time.
          default: restart
          selector:
            select:
              options:
                - label: One alert at a time
                  value: restart
                - label: One alert per triggering entity
                  value: parallel

        duration_issue_state:
          name: "Time Delay before Alert is Sent\"""",
)
s = must(
    s,
    "  repeat_count: 0\n  camera: !input camera\n",
    """  repeat_count: 0
  run_mode: !input run_mode
  per_entity: "{{ run_mode == 'parallel' }}"
  camera: !input camera
""",
)
# the triggering entity, the per-entity tag and bell id, and persistence off per entity
s = must(
    s,
    "      persist_entity_id: '{{ trigger.get(\"entity_id\", \"\") }}'\n",
    """      persist_entity_id: '{{ trigger.get("entity_id", "") }}'
      alert_key: "{{ trigger.get('entity_id', '') | string }}"
      notification_tag: >-
        {{ notification_id_template ~ ('-' ~ (trigger.get('entity_id', '') | string).split('.')[-1]
           if per_entity and trigger.get('entity_id') and notification_id_template != '' else '') }}
      include_persistence: "{{ include_persistence and not per_entity }}"
""",
)
s = must(
    s,
    "      webui_notification_id: '{{ \"webui_\" ~ (notification_id_template if notification_id_template != \"\" else context.id) }}'",
    "      webui_notification_id: '{{ \"webui_\" ~ (notification_tag if notification_tag != \"\" else context.id) }}'",
)
# the first notification_tag line (main path) is now set after the trigger entity is known: drop the early one
s = must(s, "      number_of_notify_services: '{{ notify_services_list | count }}'\n      notification_tag: '{{ notification_id_template }}'\n      trigger_fired_at:",
         "      number_of_notify_services: '{{ notify_services_list | count }}'\n      trigger_fired_at:")

STOP_EVENT = "smart_repeating_alerts_stop"
FIRE = f"""- if:
    - condition: template
      value_template: "{{{{ per_entity and alert_key != '' }}}}"
  then:
    - event: {STOP_EVENT}
      event_data:
        automation: "{{{{ this.entity_id }}}}"
        entity: "{{{{ alert_key }}}}"
"""


def block(text: str, ind: str) -> str:
    return "".join(ind + ln + "\n" if ln else "\n" for ln in text.rstrip("\n").split("\n"))


# a clear or resolution for an entity stops that entity's alert run
for marker in ("      # ── CLEAR TRIGGER FIRED", "      # ── RESOLUTION TRIGGER FIRED"):
    i = s.index(marker)
    j = s.index("        sequence:\n", i) + len("        sequence:\n")
    s = s[:j] + block(FIRE, "          ") + s[j:]
# a new trigger for the same entity replaces its running alert
alert_at = s.index("    # ── ALERT TRIGGER FIRED")
j = s.index("    default:\n", alert_at) + len("    default:\n")
s = s[:j] + block(FIRE, "    ") + s[j:]

LISTEN = f"""- trigger: event
  event_type: {STOP_EVENT}
  event_data:
    automation: "{{{{ this.entity_id }}}}"
    entity: "{{{{ alert_key }}}}"
"""
CHECK = """- if:
    - condition: template
      value_template: "{{ wait.trigger is not none and wait.trigger.event is defined and wait.trigger.event.event_type == 'smart_repeating_alerts_stop' }}"
  then:
    - stop: "Cleared or replaced by a newer alert for this entity"
"""
lines = s.split("\n")
alert_line = next(n for n, ln in enumerate(lines) if ln.startswith("    # ── ALERT TRIGGER FIRED"))
out: list[str] = []
n = 0
waits = delays = 0
while n < len(lines):
    ln = lines[n]
    st = ln.lstrip()
    ind = ln[: len(ln) - len(st)]
    if n > alert_line and st == "- wait_for_trigger:":
        # copy the block, add the stop listener as the first trigger, then the stop check after it
        item_ind = ind + "    "
        out.append(ln)
        out += block(LISTEN, item_ind).rstrip("\n").split("\n")
        n += 1
        while n < len(lines) and (lines[n].strip() == "" or len(lines[n]) - len(lines[n].lstrip()) > len(ind)):
            out.append(lines[n])
            n += 1
        out += block(CHECK, ind).rstrip("\n").split("\n")
        waits += 1
        continue
    if n > alert_line and st in ("- delay: !input duration_issue_state", "- delay: !input time_between_repeat_notification"):
        dur = st.split("!input ", 1)[1]
        out += block(f"""- wait_for_trigger:
{LISTEN.rstrip().replace(chr(10), chr(10) + '    ').join(['    ', ''])}
  timeout: !input {dur}
  continue_on_timeout: true
""", ind).rstrip("\n").split("\n")
        out += block(CHECK, ind).rstrip("\n").split("\n")
        delays += 1
        n += 1
        continue
    out.append(ln)
    n += 1
s = "\n".join(out)
if (waits, delays) != (4, 3):
    sys.exit(f"build: expected 4 button waits and 3 delays in the alert path, found {waits} and {delays}")

# ── modern syntax ────────────────────────────────────────────────────────────────────────────────────────────────────
s = re.sub(r"^(\s*-?\s*)service: ", r"\1action: ", s, flags=re.M)
s = re.sub(r"^(\s*-?\s*)platform: ", r"\1trigger: ", s, flags=re.M)
s = must(s, "\naction:\n  - variables:\n", "\nactions:\n  - variables:\n")

# camera variables first: android_channel, notification_group and titles may use camera_name
CAM_VARS = [ln for ln in s.split("\n") if ln.startswith(("  camera: !input camera", "  camera_object_id:", "  camera_name:"))]
if len(CAM_VARS) != 3:
    sys.exit(f"build: expected 3 camera variables, found {len(CAM_VARS)}")
for ln in CAM_VARS:
    s = s.replace(ln + "\n", "", 1)
s = must(s, "\nvariables:\n", "\nvariables:\n" + "\n".join(CAM_VARS) + "\n")

OUT.write_text(s)
print(f"wrote {OUT.name}: {len(s.splitlines())} lines, {added} notification sends extended")
