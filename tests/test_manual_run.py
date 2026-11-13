"""A manual Run (Run actions in the UI, automation.trigger) sends the alert with its snapshot, and skips the cooldown."""

import shutil
import asyncio
from typing import Any
from pathlib import Path

from homeassistant.core import ServiceCall
from homeassistant.setup import async_setup_component

ROOT = Path(__file__).resolve().parent.parent


async def _setup(hass: Any, tmp_path: Path) -> tuple[list[ServiceCall], list[ServiceCall]]:
    hass.config.config_dir = str(tmp_path)
    dst = tmp_path / "blueprints" / "automation" / "LTek"
    dst.mkdir(parents=True)
    shutil.copy(ROOT / "smart-repeating-alerts-ltek.yaml", dst)
    sent: list[ServiceCall] = []
    snaps: list[ServiceCall] = []
    hass.services.async_register("notify", "phone", lambda call: sent.append(call))
    hass.services.async_register("camera", "snapshot", lambda call: snaps.append(call))
    hass.states.async_set("binary_sensor.motion", "off")
    hass.states.async_set("camera.door", "idle", {"friendly_name": "Door"})
    assert await async_setup_component(hass, "automation", {"automation": [{
        "id": "cam", "alias": "Camera",
        "use_blueprint": {"path": "LTek/smart-repeating-alerts-ltek.yaml", "input": {
            "alert_trigger": [{"trigger": "state", "entity_id": "binary_sensor.motion", "to": "on"}],
            "notify_services": ["notify.phone"],
            "notification_title": "Motion",
            "camera": "camera.door",
            "snapshot_delay": 0,
            "cooldown_time": 180,
        }},
    }]})
    await hass.async_block_till_done()
    return sent, snaps


async def _wait(calls: list, n: int) -> None:
    for _ in range(60):
        if len(calls) >= n:
            break
        await asyncio.sleep(0.05)
    await asyncio.sleep(0.2)


async def test_manual_run_sends_with_snapshot(hass: Any, tmp_path: Path) -> None:
    sent, snaps = await _setup(hass, tmp_path)
    await hass.services.async_call("automation", "trigger", {"entity_id": "automation.camera"})
    await _wait(sent, 1)
    assert len(snaps) == 1
    assert len(sent) == 1
    assert sent[0].data["data"]["image"] == "/media/local/snapshots/door_last.jpg"


async def test_manual_run_skips_cooldown(hass: Any, tmp_path: Path) -> None:
    sent, snaps = await _setup(hass, tmp_path)
    hass.states.async_set("binary_sensor.motion", "on")
    await _wait(sent, 1)
    assert len(sent) == 1
    await hass.services.async_call("automation", "trigger", {"entity_id": "automation.camera"})
    await _wait(sent, 2)
    assert len(sent) == 2 and len(snaps) == 2


async def test_real_trigger_still_respects_cooldown(hass: Any, tmp_path: Path) -> None:
    sent, _ = await _setup(hass, tmp_path)
    hass.states.async_set("binary_sensor.motion", "on")
    await _wait(sent, 1)
    hass.states.async_set("binary_sensor.motion", "off")
    hass.states.async_set("binary_sensor.motion", "on")
    await _wait(sent, 2)
    assert len(sent) == 1
