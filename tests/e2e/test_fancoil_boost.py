"""Behavioral tests for packages/coordinators/fancoil_boost.yaml.

Covers the documented state machine contract:

  Activation (OR logic, each trigger starts the anti-cycling timer):
    1. Reactive temp:     delta > threshold
    2. Reactive humidity: humidity > threshold + hysteresis/2
    3. Predictive:        radiant saturated AND above target AND not cooling down
  Anti-cycling:  the timer cancels if the condition clears before it elapses
  Deactivation (AND logic): delta <= 0 AND humidity <= threshold - hysteresis/2
  Season override: leaving cooling season ends boost immediately (no delay)

The harness compresses min_time_in_state to 2 s (prod: 600 s). The radiant
PID target is 24.0 C, so absolute temps map to deltas: 26.0 => +2.0.
With humidity threshold 60 and hysteresis 5, boost activates above 62.5
and may deactivate at or below 57.5.
"""

import asyncio

import pytest
from aioesphomeapi import ClimateMode

NAN = float("nan")

# Object ids exposed by the harness (zone_slug "test_zone", zone_name "Test Zone").
STATE = "test_zone_boost_state"
AUTOMATION = "test_zone_boost_automation_state"
OVERRIDE_SWITCH = "radiant_override"
OVERRIDE_VALUE = "radiant_override_value"
FANCOIL = "fancoil_pid"

pytestmark = pytest.mark.asyncio


async def setup_zone(h, *, cooling: bool):
    """Baseline: comfortable zone, sane thresholds, predictive disarmed."""
    await h.call("set_temp_threshold", value=1.0)
    await h.call("set_humidity_threshold", value=60.0)
    await h.call("set_predictive_minutes", value=999.0)
    await h.call("set_humidity", value=50.0)
    await h.call("set_temperature", value=24.0)
    await h.call("set_cooling_mode", value=cooling)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle")


async def reach_boost(h):
    """Drive the zone into Fancoil Boost via the reactive temp trigger."""
    await h.call("set_temperature", value=26.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Boost Active")


async def test_reactive_temp_activation_locks_radiant_and_enables_fancoil(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=False)

    # Hot room, but heating season: must NOT trigger.
    await h.call("set_temperature", value=26.0)
    await asyncio.sleep(0.5)
    assert h.states[AUTOMATION].state == "Idle"
    assert h.states[STATE].state == "Radiant Only"

    # Cooling season starts: trigger fires, anti-cycling timer runs, boost engages.
    await h.call("set_cooling_mode", value=True)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)

    # Hardware side effects of the transition:
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is True)
    await h.wait_for_value(OVERRIDE_VALUE, 100.0)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.COOL)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Boost Active")


async def test_anti_cycling_timer_cancels_when_condition_clears(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)

    await h.call("set_temperature", value=26.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")

    # Condition clears before the 2 s anti-cycling delay elapses.
    await h.call("set_temperature", value=23.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle")

    # Even after the would-be delay, the transition must NOT have happened.
    await asyncio.sleep(2.5)
    assert h.states[STATE].state == "Radiant Only"
    assert h.states[FANCOIL].mode == ClimateMode.OFF
    assert h.states[OVERRIDE_SWITCH].state is False


async def test_reactive_humidity_activation(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)

    # Temp at target; humidity above threshold + hysteresis/2 (62.5).
    await h.call("set_humidity", value=64.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (reactive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=5)


async def test_predictive_activation_on_sustained_saturation(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)

    # Reactive temp trigger out of reach; predictive delay 0.05 min = 3 s.
    await h.call("set_temp_threshold", value=5.0)
    await h.call("set_predictive_minutes", value=0.05)

    # Above target (delta +2 < threshold 5) with the radiant PID saturated.
    await h.call("set_temperature", value=26.0)
    await h.call("set_radiant_cool_output", value=0.96)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Activating (predictive)")
    await h.wait_for(STATE, lambda s: s.state == "Fancoil Boost", timeout=6)


async def test_deactivation_requires_temp_and_humidity(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await reach_boost(h)

    # Temp back at target, but humidity above the lower band (57.5):
    # AND logic must keep boost active.
    await h.call("set_humidity", value=70.0)
    await h.call("set_temperature", value=23.0)
    await asyncio.sleep(1.0)
    assert h.states[STATE].state == "Fancoil Boost"
    assert h.states[AUTOMATION].state == "Boost Active"

    # Humidity drops below the band: both conditions met, deactivation runs.
    await h.call("set_humidity", value=50.0)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Deactivating")
    await h.wait_for(STATE, lambda s: s.state == "Radiant Only", timeout=5)

    # Hardware released: override off, fancoil off, automation idle.
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is False)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.OFF)
    await h.wait_for(AUTOMATION, lambda s: s.state == "Idle")


async def test_season_change_ends_boost_immediately(run_harness):
    h = await run_harness("fancoil_boost")
    await setup_zone(h, cooling=True)
    await reach_boost(h)

    # Cooling season ends: safety override bypasses the anti-cycling delay.
    await h.call("set_cooling_mode", value=False)
    await h.wait_for(STATE, lambda s: s.state == "Radiant Only", timeout=1.5)
    await h.wait_for(OVERRIDE_SWITCH, lambda s: s.state is False)
    await h.wait_for(FANCOIL, lambda s: s.mode == ClimateMode.OFF)
