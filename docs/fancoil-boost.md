# Fancoil Boost Coordinator

The "Base + Boost" pattern: radiant floor provides efficient baseline cooling, fancoils activate automatically when conditions demand more capacity.

## The Problem

Radiant floor cooling is energy-efficient and comfortable, but limited by physics:
- **Slow response**: Thermal mass means radiant can't react quickly to sudden heat gains
- **Humidity ceiling**: High humidity raises the dew point, forcing warmer supply water to avoid condensation, which reduces cooling capacity
- **Capacity limit**: When PID output reaches 100%, radiant simply can't cool any further

Fancoils are fast and can dehumidify, but are less efficient and noisier than radiant.

## The Base + Boost Innovation

Instead of choosing one system or the other, the coordinator treats them as **complementary layers**:

```
┌─────────────────────────────────────────────────────┐
│                    Zone Output                       │
│                                                      │
│  ┌──────────────────────────────────────────┐       │
│  │ BASE LAYER: Radiant Floor (always active) │       │
│  │  - PID-controlled in normal mode          │       │
│  │  - Locked at 100% during boost            │       │
│  └──────────────────────────────────────────┘       │
│                                                      │
│  ┌──────────────────────────────────────────┐       │
│  │ BOOST LAYER: Fancoil (on-demand)          │       │
│  │  - OFF in normal mode                     │       │
│  │  - PID-controlled COOL during boost       │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

**Normal mode (Radiant Only):** PID controls radiant output. Fancoil is OFF.

**Boost mode (Fancoil Boost):** Radiant locked at 100% (maximum cooling). Fancoil PID activates in COOL mode. Both systems work together.

## Activation Triggers

Boost activates when **any one** condition is met (OR logic):

### 1. Reactive: Temperature Delta

```
temp_delta > temp_threshold
```

The room is too warm for radiant alone. This is the most direct trigger - when the temperature gap between current and target exceeds a configurable threshold, the fancoil is needed.

### 2. Reactive: Humidity

```
humidity > humidity_threshold + (hysteresis / 2)
```

High humidity limits radiant cooling capacity by raising the dew point. Fancoils can dehumidify while cooling, lowering the dew point and enabling more aggressive radiant operation. The hysteresis prevents oscillation around the threshold.

### 3. Predictive: PID Saturation

```
radiant_output >= 95% for X minutes AND temperature not decreasing
```

This is the intelligent trigger. When the radiant PID has been running at maximum output for a sustained period and the room isn't getting cooler, the system is at capacity. The coordinator activates boost **before** the temperature delta exceeds the reactive threshold, improving comfort by acting proactively.

**Safety check**: The predictive trigger only fires if temperature is flat or rising (trend >= -0.005 C/min). If the room IS cooling, just slowly, the radiant is making progress and boost isn't needed yet.

## Deactivation Logic

Boost deactivates when **both** conditions are met (AND logic):

```
temp_delta <= 0  AND  humidity <= humidity_threshold - (hysteresis / 2)
```

- **Temperature**: The target has been reached (room is at or below setpoint)
- **Humidity**: Below the lower bound of the hysteresis dead band

Both conditions must be satisfied to prevent premature deactivation. If temperature is OK but humidity is still high, the fancoil keeps running to dehumidify.

## Anti-Oscillation Protection

### Humidity Hysteresis Dead Band

With `humidity_threshold: 65%` and `humidity_hysteresis: 5.0`:

```
          62.5%      65%      67.5%
Deactivate ←|         |         |→ Activate
             ▼         ▼         ▼
─────────────[===dead band===]──────────
```

- Activate at > 67.5% (threshold + hysteresis/2)
- Deactivate at <= 62.5% (threshold - hysteresis/2)
- The 5% dead band prevents rapid switching

### Minimum Time-in-State

Default: 10 minutes (`min_time_in_state_seconds: 600`)

After any mode transition, the coordinator ignores trigger conditions for this duration. This prevents mechanical wear from rapid cycling and gives the system time to stabilize.

## Dependency

This component **automatically includes** `trend_sensor.yaml` from `../components/`. The trend sensor monitors the zone temperature for rate-of-change data used by the predictive trigger.

**Dependency chain:**
```
fancoil_boost.yaml (packages/coordinators/)
└── trend_sensor.yaml (packages/components/, auto-included)
```

## Parameter Reference

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `zone_slug` | string | Zone identifier for entity IDs (e.g., `living_room`) |
| `zone_name` | string | Human-readable zone name (e.g., `Living Room`) |
| `temperature_sensor` | ID | Zone temperature sensor |
| `humidity_sensor` | ID | Zone humidity sensor |
| `radiant_pid_id` | ID | Radiant PID climate entity (for `.target_temperature`) |
| `radiant_pid_cool_sensor` | ID | PID cool output sensor (0-1 range) |
| `fancoil_pid_id` | ID | Fancoil PID climate entity (set to COOL/OFF) |
| `radiant_override_value_id` | ID | Number entity to set radiant override percentage |
| `radiant_override_switch_id` | ID | Switch to enable/disable radiant override |
| `radiant_pwm_id` | ID | Slow PWM output for radiant floor |
| `cooling_mode_sensor` | ID | Binary sensor: true = cooling season |
| `temp_threshold_sensor` | ID | Sensor providing temperature delta threshold |
| `humidity_threshold_sensor` | ID | Sensor providing humidity threshold |
| `predictive_minutes_sensor` | ID | Sensor providing predictive boost duration |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_time_in_state_seconds` | int | `600` | Anti-cycling minimum (seconds) |
| `humidity_hysteresis` | float | `5.0` | Dead band around humidity threshold (% RH) |
| `saturated_output_threshold` | float | `0.95` | PID output considered "saturated" (0-1) |

## Diagnostic Sensors

The coordinator exposes 7 diagnostic entities for monitoring and dashboards:

| Entity | Type | Description |
|--------|------|-------------|
| `{zone_slug}_boost_active_sensor` | binary_sensor | Whether boost mode is active |
| `{zone_slug}_cooling_mode` | text_sensor | "Fancoil Boost" or "Radiant Only" |
| `{zone_slug}_temp_delta` | sensor | Current - target temperature (positive = needs cooling) |
| `{zone_slug}_time_in_mode` | sensor | Minutes in current mode |
| `{zone_slug}_saturation_duration` | sensor | Minutes PID output has been at saturation |
| `{zone_slug}_radiant_output_pct` | sensor | Radiant PID output as percentage |
| `{zone_slug}_temp_trend` | sensor | Temperature rate of change (C/min) |

## Usage Example

### Complete Single-Zone Integration

This example shows how to wire up all the required entities for one cooling zone:

```yaml
# Prerequisites: PID controllers, override entities, and threshold sensors
# must be defined elsewhere in your configuration.

# Zone sensors (from failover_sensor or direct)
packages:
  temp_failover: !include
    file: packages/components/failover_sensor.yaml
    vars:
      sensor_id: "living_room_temp"
      sensor_name: "Living Room Temperature"
      unit_of_measurement: "°C"
      device_class: "temperature"
      primary_sensor: ha_living_room_temp
      secondary_sensor: modbus_living_room_temp

  humidity_failover: !include
    file: packages/components/failover_sensor.yaml
    vars:
      sensor_id: "living_room_humidity"
      sensor_name: "Living Room Humidity"
      unit_of_measurement: "%"
      device_class: "humidity"
      primary_sensor: ha_living_room_humidity
      secondary_sensor: modbus_living_room_humidity

  # The boost coordinator
  boost: !include
    file: packages/coordinators/fancoil_boost.yaml
    vars:
      zone_slug: "living_room"
      zone_name: "Living Room"
      temperature_sensor: living_room_temp
      humidity_sensor: living_room_humidity
      radiant_pid_id: pid_radiant_living_room
      radiant_pid_cool_sensor: pid_radiant_living_room_cool
      fancoil_pid_id: pid_fancoil_living_room
      radiant_override_value_id: living_room_radiant_override_value
      radiant_override_switch_id: living_room_radiant_override
      radiant_pwm_id: slow_pwm_living_room
      cooling_mode_sensor: summer_mode
      temp_threshold_sensor: fancoil_boost_threshold
      humidity_threshold_sensor: fancoil_humidity_threshold
      predictive_minutes_sensor: predictive_boost_minutes
```

### Multiple Zones

Include the coordinator once per zone with zone-specific parameters:

```yaml
packages:
  living_room_boost: !include
    file: packages/coordinators/fancoil_boost.yaml
    vars:
      zone_slug: "living_room"
      zone_name: "Living Room"
      temperature_sensor: living_room_temp
      humidity_sensor: living_room_humidity
      # ... (remaining zone-specific IDs)

  kitchen_boost: !include
    file: packages/coordinators/fancoil_boost.yaml
    vars:
      zone_slug: "kitchen"
      zone_name: "Kitchen"
      temperature_sensor: kitchen_temp
      humidity_sensor: kitchen_humidity
      # ... (remaining zone-specific IDs)
```

Shared threshold sensors (`temp_threshold_sensor`, `humidity_threshold_sensor`, `predictive_minutes_sensor`) can point to the same entities across all zones, or each zone can have independent thresholds.

## Integration Tips

- **Threshold sensors**: Use Home Assistant `input_number` entities for thresholds to allow runtime tuning from dashboards without reflashing. Typical starting values: temp threshold 1.5°C, humidity threshold 65%, predictive minutes 20
- **Radiant override**: The override mechanism (value + switch) locks radiant output at 100% during boost. When boost deactivates, the switch is turned off and the PID resumes normal control
- **Season awareness**: The `cooling_mode_sensor` should be a binary sensor that's true during cooling season. The coordinator automatically exits boost and stops processing when cooling mode is false
- **Logging**: All mode transitions are logged at INFO level with detailed trigger information. Use `logger` component to monitor coordinator decisions
- **Multiple zones**: Each zone operates independently. One zone can be in boost while others remain in normal mode
- **Failover integration**: Wire `temperature_sensor` and `humidity_sensor` to failover sensor outputs for reliable operation even when sensor sources fail
