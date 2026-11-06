"""Smart Repeating Alerts loads as a Home Assistant blueprint, and filled-in automations pass Home Assistant's validation.

    pytest tests                                 # the blueprint and sample automations
    SMART_REPEATING_ALERTS_CONVERTED=<dir> pytest tests    # also every converted automation in <dir> (kept outside the repo)
"""

import os
from typing import Any
from pathlib import Path

import pytest
from homeassistant.util.yaml import load_yaml
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA, async_validate_config_item

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / "smart-repeating-alerts-ltek.yaml"


def _blueprint() -> Blueprint:
    return Blueprint(load_yaml(str(BP)), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)


async def _validate(hass: Any, cfg: dict) -> dict:
    ub = cfg["use_blueprint"]
    filled = BlueprintInputs(_blueprint(), {"use_blueprint": {"path": "LTek/smart-repeating-alerts-ltek.yaml", "input": ub.get("input") or {}}})
    filled.validate()
    sub = filled.async_substitute()
    res = await async_validate_config_item(hass, cfg.get("id", "t"), {"id": cfg.get("id", "t"), "alias": cfg.get("alias", "t"), **sub})
    assert res is not None and not getattr(res, "validation_error", None), getattr(res, "validation_error", res)
    return sub


def test_every_input_has_a_default() -> None:
    """A new automation can be created with no inputs (the panel's + New does this)."""
    bp = _blueprint()
    missing = [k for k, v in bp.inputs.items() if v is None or "default" not in v]
    assert missing == []


async def test_minimal(hass: Any) -> None:
    sub = await _validate(hass, {"use_blueprint": {"input": {}}})
    assert sub["mode"] == "restart"


async def test_camera_and_extras(hass: Any) -> None:
    sub = await _validate(hass, {"use_blueprint": {"input": {
        "alert_trigger": [{"trigger": "state", "entity_id": "binary_sensor.motion", "to": "on"}],
        "camera": "camera.patio", "snapshot_delay": 1, "cooldown_time": 120, "test_mode": True,
        "notify_services": ["family", "notify.tv"], "notification_group": "Patio",
        "include_action_buttons": ["enable_action_button_1"], "action_button_1_label": "Cams",
        "action_button_1_uri": "/dashboard-home/cameras", "android_alarm_stream": True, "android_priority": "high",
    }}})
    text = str(sub)
    assert "camera.snapshot" in text and "service:" not in text and "platform:" not in text


CONVERTED = os.environ.get("SMART_REPEATING_ALERTS_CONVERTED")


@pytest.mark.skipif(not CONVERTED, reason="set SMART_REPEATING_ALERTS_CONVERTED to check converted automations")
async def test_converted(hass: Any) -> None:
    """Every input fills the blueprint; full validation where this test's Home Assistant knows every type used.

    Purpose-specific triggers and conditions (door.closed, moisture.detected, ...) are newer than the Home Assistant
    the tests run on; those automations are listed and still get the blueprint check (inputs and substitution).
    """
    files = sorted(Path(CONVERTED).glob("*.yaml"))
    assert files
    partial = []
    for f in files:
        (cfg,) = load_yaml(str(f))
        filled = BlueprintInputs(_blueprint(), {"use_blueprint": {"path": "x", "input": cfg["use_blueprint"]["input"] or {}}})
        filled.validate()
        filled.async_substitute()
        try:
            await _validate(hass, cfg)
        except Exception as err:  # noqa: BLE001
            if any(x in str(err) for x in ("Invalid trigger", "Invalid condition", "does not provide trigger", "does not provide condition", "not found")):
                partial.append(f"{f.name}: {str(err).splitlines()[0][:90]}")
                continue
            raise AssertionError(f"{f.name}: {err}") from err
    print(f"\n{len(files) - len(partial)} fully validated; blueprint check only (newer types):", *partial, sep="\n  ")
