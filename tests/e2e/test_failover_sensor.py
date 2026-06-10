"""Behavioral tests for packages/components/failover_sensor.yaml.

Exercises the full tier table documented in the package header:

    | Primary | Secondary | Active Tier | Output      |
    |---------|-----------|-------------|-------------|
    | Valid   | Valid     | Primary     | Primary val |
    | Valid   | NaN       | Primary     | Primary val |
    | NaN     | Valid     | Secondary   | Secondary   |
    | NaN     | NaN       | Emergency   | NaN         |

plus the recovery transitions back out of Secondary/Emergency.
"""

import pytest

NAN = float("nan")

pytestmark = pytest.mark.asyncio


async def test_failover_tier_cascade_and_recovery(run_harness):
    h = await run_harness("failover_sensor")

    # Both stubs start as NaN -> Emergency tier, NaN output.
    await h.wait_for("test_temp_active_sensor_tier", lambda s: s.state == "Emergency")
    await h.wait_for_value("test_temp", NAN)

    # Primary becomes valid -> Primary tier, primary value.
    await h.call("set_primary", value=21.5)
    await h.wait_for("test_temp_active_sensor_tier", lambda s: s.state == "Primary")
    await h.wait_for_value("test_temp", 21.5)

    # Secondary valid too -> primary still wins.
    await h.call("set_secondary", value=19.0)
    await h.wait_for_value("test_temp", 21.5)

    # Primary dies -> failover to Secondary, secondary value.
    await h.call("set_primary", value=NAN)
    await h.wait_for("test_temp_active_sensor_tier", lambda s: s.state == "Secondary")
    await h.wait_for_value("test_temp", 19.0)

    # Secondary dies as well -> Emergency, NaN output.
    await h.call("set_secondary", value=NAN)
    await h.wait_for("test_temp_active_sensor_tier", lambda s: s.state == "Emergency")
    await h.wait_for_value("test_temp", NAN)

    # Primary recovers -> straight back to Primary.
    await h.call("set_primary", value=22.0)
    await h.wait_for("test_temp_active_sensor_tier", lambda s: s.state == "Primary")
    await h.wait_for_value("test_temp", 22.0)
