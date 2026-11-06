"""Behavior in a real Home Assistant: one alert per triggering entity, and the classic one-alert-at-a-time mode."""

import shutil
import asyncio
from typing import Any
from datetime import timedelta
from pathlib import Path

import pytest
from homeassistant.core import ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

ROOT = Path(__file__).resolve().parent.parent
WIN = ["binary_sensor.window_kitchen", "binary_sensor.window_bedroom"]


async def _setup(hass: Any, tmp_path: Path, run_mode: str) -> list[ServiceCall]:
    hass.config.config_dir = str(tmp_path)
    dst = tmp_path / "blueprints" / "automation" / "LTek"
    dst.mkdir(parents=True)
    shutil.copy(ROOT / "smart-repeating-alerts-ltek.yaml", dst)
    calls: list[ServiceCall] = []
    hass.services.async_register("notify", "phone", lambda call: calls.append(call))
    for e in WIN:
        hass.states.async_set(e, "off", {"friendly_name": e.split("_")[-1].title()})
    assert await async_setup_component(hass, "automation", {"automation": [{
        "id": "w", "alias": "Windows",
        "use_blueprint": {"path": "LTek/smart-repeating-alerts-ltek.yaml", "input": {
            "run_mode": run_mode,
            "alert_trigger": [{"trigger": "state", "entity_id": WIN, "to": "on"}],
            "clear_trigger": [{"trigger": "state", "entity_id": WIN, "to": "off"}],
            "notify_services": ["notify.phone"],
            "notification_id": "window",
            "notification_title": "{{ friendly_name }} is open",
            "repeat_notification": True,
            "time_between_repeat_notification": {"minutes": 1},
            "include_action_buttons": ["enable_action_button_1"],
            "action_button_1_label": "Bypass",
        }},
    }]})
    await hass.async_block_till_done()
    NOW[0] = dt_util.utcnow()
    return calls


def _sent(calls: list[ServiceCall]) -> list[tuple[str, str]]:
    """(title or 'CLEAR', tag) per notify call."""
    out = []
    for c in calls:
        d = c.data.get("data") or {}
        out.append(("CLEAR" if c.data.get("message") == "clear_notification" else c.data.get("title", "").strip(), d.get("tag")))
    return out


async def _settle(hass: Any, seconds: float = 0.5) -> None:
    """Let the runs work. Not async_block_till_done: it waits for every task, and an alert run waits for minutes."""
    for _ in range(int(seconds / 0.05)):
        await asyncio.sleep(0.05)


async def _wait_for(calls: list, n: int, hass: Any) -> None:
    for _ in range(100):
        if len(calls) >= n:
            break
        await asyncio.sleep(0.05)
    await _settle(hass, 0.2)


NOW = [dt_util.utcnow()]


async def _minutes(hass: Any, n: float) -> None:
    NOW[0] = NOW[0] + timedelta(minutes=n)
    async_fire_time_changed(hass, NOW[0])
    await _settle(hass)


@pytest.mark.parametrize("expect_both", [True])
async def test_one_alert_per_entity(hass: Any, tmp_path: Path, expect_both: bool) -> None:
    """Two windows: two alerts with their own tags; closing one clears only it, the other keeps repeating."""
    calls = await _setup(hass, tmp_path, "parallel")
    hass.states.async_set(WIN[0], "on", {"friendly_name": "Kitchen"})
    await _settle(hass)
    hass.states.async_set(WIN[1], "on", {"friendly_name": "Bedroom"})
    await _settle(hass)
    assert _sent(calls) == [("Kitchen is open", "window-window_kitchen"), ("Bedroom is open", "window-window_bedroom")]
    # buttons are per run
    acts = [c.data["data"]["actions"][0]["action"] for c in calls]
    assert acts[0] != acts[1]

    calls.clear()
    hass.states.async_set(WIN[0], "off", {"friendly_name": "Kitchen"})
    await _settle(hass)
    assert _sent(calls) == [("CLEAR", "window-window_kitchen")]

    calls.clear()
    for _ in range(3):
        await _minutes(hass, 1.1)
    sent = _sent(calls)
    assert sent and all(tag == "window-window_bedroom" for _, tag in sent), sent  # only Bedroom repeats


async def test_one_alert_at_a_time_unchanged(hass: Any, tmp_path: Path) -> None:
    """The default keeps Repeating Alerts' behavior: one tag, a second window replaces the first."""
    calls = await _setup(hass, tmp_path, "restart")
    hass.states.async_set(WIN[0], "on", {"friendly_name": "Kitchen"})
    await _settle(hass)
    hass.states.async_set(WIN[1], "on", {"friendly_name": "Bedroom"})
    await _settle(hass)
    assert [t for t, _ in _sent(calls)] == ["Kitchen is open", "Bedroom is open"]
    assert {tag for _, tag in _sent(calls)} == {"window"}
