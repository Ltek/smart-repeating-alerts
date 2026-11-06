#!/usr/bin/env python3
"""Convert Repeating Alerts and Smart Camera Notifications automations to Smart Repeating Alerts, one YAML file each.

    python3 tools/convert.py <automations.yaml> <output dir>

Each file is one automation (same id and alias) using LTek/smart-repeating-alerts-ltek.yaml, with a comment block listing what
was mapped. Paste it over the old automation in automations.yaml (or into the automation's YAML editor).
Nothing is written next to automations.yaml.
"""

import re
import sys
import copy
from pathlib import Path

import yaml

NEW_PATH = "LTek/smart-repeating-alerts-ltek.yaml"
RA_PATH = "LTek/repeating-alerts-ltek.yaml"
CAM_PATH = "LTek/smart-camera-notifications-ltek.yaml"
ROOT = Path(__file__).resolve().parent.parent


class Loader(yaml.SafeLoader):
    pass


class Tagged(str):
    """A !tag value (e.g. !secret), kept as written."""


Loader.add_multi_constructor("!", lambda loader, tag, node: Tagged(f"!{tag} {node.value}"))


class Dumper(yaml.SafeDumper):
    pass


def _str(dumper, data):
    if isinstance(data, Tagged):
        tag, _, val = str(data).partition(" ")
        return dumper.represent_scalar(tag, val)
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


Dumper.add_representer(str, _str)
Dumper.add_representer(Tagged, _str)


def blueprint_inputs() -> set[str]:
    bp = yaml.load((ROOT / "smart-repeating-alerts-ltek.yaml").read_text(), Loader=Loader)["blueprint"]

    def walk(d):
        for k, v in (d or {}).items():
            if isinstance(v, dict) and "input" in v:
                yield from walk(v["input"])
            else:
                yield k

    return set(walk(bp["input"]))


def convert_ra(inp: dict, notes: list[str]) -> dict:
    out = dict(inp)
    if out.pop("android_priority", None) is not None:
        out["android_priority"] = "high"
        notes.append("android_priority: was 'urgent' (did nothing in Repeating Alerts) → high")
    for old, new in (("enable_android_wake", "wake_screen_notification"),
                     ("enable_webui_notifications", "enable_webui_normal_notifications")):
        if old in out:
            v = out.pop(old)
            if new not in out:
                out[new] = v
            notes.append(f"{old} (no longer in Repeating Alerts) → {new}")
    for k in ("android_alarm_stream", "android_vibration_pattern", "android_led_color"):
        if k in out:
            notes.append(f"{k}: did nothing in Repeating Alerts; Smart Repeating Alerts uses it")
    return out


def convert_cam(inp: dict, notes: list[str]) -> dict:
    g = inp.get
    out: dict = {}
    out["alert_trigger"] = g("trigger_additional", [])
    conds = []
    if g("use_conditions") and g("custom_conditions"):
        conds += g("custom_conditions")
    if g("condition"):
        conds += g("condition") if isinstance(g("condition"), list) else [g("condition")]
        notes.append("Notification Conditions merged into Optional Trigger Conditions")
    if conds:
        out["condition_send_notification"] = conds
    cam = g("camera")
    out["camera"] = cam
    if g("delay"):
        out["snapshot_delay"] = g("delay")
    if g("file_path"):
        out["snapshot_file_path"] = g("file_path")
    for k in ("save_archive_file", "archive_file_path", "notify_device", "notification_title", "notification_message"):
        if k in inp:
            out[k] = inp[k]
    out["notification_click_url"] = g("notification_click_url") or f"entityId:{cam}"
    # one alert per motion: no repeats, no tag, nothing auto-cleared, no Cancel button
    out["repeat_notification"] = False
    out["notification_id"] = ""
    out["enable_auto_clear"] = False
    out["include_cancel_button"] = False
    gap = max(int(g("delay_notification", 60) or 0), int(g("cooldown_time", 30) or 0))
    out["cooldown_time"] = gap
    notes.append(f"cooldown_time: {gap} s (the larger of delay_notification {g('delay_notification', 60)} and "
                 f"cooldown_time {g('cooldown_time', 30)})")
    # buttons (newer *_title/_uri names first, then the old action_title_N / action_uri_N)
    if g("include_action_buttons"):
        out["include_action_buttons"] = g("include_action_buttons")
    for n in (1, 2, 3):
        label = g(f"action_button_{n}_title") or g(f"action_title_{n}")
        uri = g(f"action_button_{n}_uri") or g(f"action_uri_{n}")
        if not g(f"action_button_{n}_title") and g(f"action_title_{n}"):
            notes.append(f"button {n}: old input action_title_{n} → action_button_{n}_label")
        if label:
            out[f"action_button_{n}_label"] = label
        if uri:
            out[f"action_button_{n}_uri"] = uri
        if g(f"action_button_{n}_action"):
            out[f"action_button_{n}_action"] = g(f"action_button_{n}_action")
    if g("action_type_2") == "FIRE_EVENT" and not g("action_button_2_action"):
        notes.append("button 2: old action_type_2 FIRE_EVENT had no action: it only fires mobile_app_notification_action")
    out["action_button_timeout"] = g("action_timeout") or {"hours": 0, "minutes": 3, "seconds": 0}
    before = g("additional_actions_before") or []
    after = g("additional_actions") or []
    if before or after:
        out["custom_action_first_trigger"] = list(before) + list(after)
        notes.append("Actions Before/After Snapshot → Custom Action - On First Trigger (they run after the snapshot)")
    # the camera blueprint's Android defaults, kept
    out["android_channel"] = g("notification_channel", "{{ camera_name }} Snapshot")
    out["notification_group"] = g("notification_group", "{{ camera_name }} Snapshot")
    out["notification_color"] = g("notification_color", "#03a9f4")
    out["notification_icon_warning"] = str(g("notification_icon", "mdi:cctv")).replace("mdi:", "")
    out["notification_persistent"] = g("notification_sticky", True)
    if g("notification_critical"):
        out["notification_interruption_level"] = "critical"
    if g("notification_sound") and g("notification_sound") != "default":
        out["ios_sound"] = g("notification_sound")
    if g("notify_group"):
        out["notify_services"] = [g("notify_group")]
        notes.append("Notify a Group or Android TV → Extra Notify Services")
    if g("android_tv"):
        notes.append("android_tv (legacy Android TV layout) is not carried over")
    if g("notify") is False:
        notes.append("Send Notifications was OFF in the old automation")
    return out


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    known = blueprint_inputs()
    data = yaml.load(src.read_text(), Loader=Loader)
    index = []
    for a in data:
        ub = a.get("use_blueprint") or {}
        path = ub.get("path")
        if path not in (RA_PATH, CAM_PATH):
            continue
        notes: list[str] = []
        inp = copy.deepcopy(ub.get("input") or {})
        new_inp = convert_ra(inp, notes) if path == RA_PATH else convert_cam(inp, notes)
        unknown = sorted(set(new_inp) - known)
        for k in unknown:
            new_inp.pop(k)
            notes.append(f"dropped {k}: not an input of Smart Repeating Alerts (it did nothing before either)")
        auto = {k: v for k, v in a.items() if k != "use_blueprint"}
        auto["use_blueprint"] = {"path": NEW_PATH, "input": new_inp}
        slug = re.sub(r"[^a-z0-9]+", "-", str(a.get("alias", a.get("id"))).lower()).strip("-")
        head = [f"# {a.get('alias')}  (id {a.get('id')})", f"# was: {path}", "# converted to Smart Repeating Alerts by tools/convert.py"]
        head += [f"#   - {n}" for n in notes] or ["#   - no changes beyond the blueprint path"]
        body = yaml.dump([auto], Dumper=Dumper, sort_keys=False, allow_unicode=True, width=120)
        (dst / f"{slug}.yaml").write_text("\n".join(head) + "\n" + body)
        index.append((slug, a.get("alias"), path.split("/")[-1], len(notes)))
    lines = ["# Smart Repeating Alerts conversions", "", "| File | Automation | Was | Notes |", "|---|---|---|---|"]
    lines += [f"| {s}.yaml | {al} | {p} | {n} |" for s, al, p, n in index]
    (dst / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(f"{len(index)} automations converted into {dst}")


if __name__ == "__main__":
    main()
