# MEV Ventilation Controller

Humidity cascade state machine controller for mechanical extract ventilation systems with event-driven escalation/de-escalation.

## What It Does

The MEV ventilation controller manages the humidity cascade state machine for a mechanical extract ventilation unit. It reads a single aggregated demand signal, applies a minimum fan speed floor, and automatically escalates through Fan Only, Dehumidifying, and Integration modes based on sustained humidity conditions.

**This is a pure controller** - it does not create hardware entities (switches, relays, DAC) or demand sensors. Those are provided externally, making it reusable across different hardware platforms and demand configurations.

## How It Works

### Fan Speed Calculation

The controller reads a single aggregated demand sensor and applies a minimum floor:

```
Demand Sensor (0-100%) ──▶ max(demand, min_fan_speed) ──▶ Final Fan Speed
                                                              │
Alarm Sensor ──▶ if alarm → 0% ────────────────────────────┘
```

The demand sensor is created externally - it could be a single proportional demand, a MAX aggregation of multiple demands, or any other 0-100% signal. The controller doesn't care how the demand was calculated.

### Humidity Cascade State Machine

The controller manages a 3-state machine for humidity control hardware:

```
┌──────────┐    escalate     ┌───────────────┐    escalate     ┌─────────────┐
│ Fan Only │ ──────────────▶ │ Dehumidifying  │ ──────────────▶ │ Integration │
│          │ ◀────────────── │               │ ◀────────────── │             │
└──────────┘   de-escalate   └───────────────┘   de-escalate   └─────────────┘
```

| State | Action | Description |
|-------|--------|-------------|
| **Fan Only** | Dehumidifier OFF, cooling OFF | Normal ventilation |
| **Dehumidifying** | Dehumidifier ON, cooling OFF | Active moisture removal |
| **Integration** | Dehumidifier ON, cooling ON | Maximum humidity reduction (summer only) |

### Escalation Rules

Escalation occurs when **both** conditions are sustained for the configured delay:
1. Final fan speed >= escalation threshold
2. Humidity rate of change > 0 (humidity is rising)

**Fan Only -> Dehumidifying**: Always available when conditions are met.

**Dehumidifying -> Integration**: Only available during cooling season (`cooling_mode_sensor` is true). This prevents energy-wasting cooling in winter.

### De-escalation Rules

De-escalation occurs when **both** conditions are sustained for the configured delay:
1. Humidity < lower bound (below the demand range)
2. Final fan speed < de-escalation threshold

**Integration -> Dehumidifying**: Also triggers immediately when cooling season ends.

**Dehumidifying -> Fan Only**: Only when not simultaneously escalating (prevents flapping).

### Timing (Event-Driven Architecture)

Transitions use an **event-driven** pattern instead of interval polling:

1. **Template binary sensors** continuously evaluate transition conditions
2. When a condition becomes true (`on_press`), a **script** starts with a configurable delay
3. If the condition stops being true (`on_release`), the script is stopped (delay cancelled)
4. Scripts use `mode: restart` - if conditions flicker, the delay timer resets

This is more reliable than counter-based polling because:
- Transitions react immediately to condition changes (not on a fixed polling interval)
- ESPHome's native `delay` action handles timing precisely
- Script restart mode naturally resets the timer when conditions flicker

Escalation and de-escalation delays are configurable via HA `input_number` entities (in minutes).

### Alarm Safety

If the alarm sensor activates, the fan speed is immediately set to 0%. Normal operation resumes when the alarm clears.

## Parameter Reference

### Required Parameters

**Identity:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_id` | string | Prefix for entity IDs (e.g., `mev`) |
| `component_name` | string | Friendly name prefix (e.g., `MEV`) |

**External Sensors (read):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `demand_sensor` | sensor ID | Aggregated demand signal (0-100%) |
| `humidity_sensor` | sensor ID | Humidity reading (for de-escalation condition) |
| `humidity_rate_sensor` | sensor ID | Humidity rate of change (for escalation condition) |
| `humidity_lower_sensor` | sensor ID | Humidity lower bound (for de-escalation condition) |
| `cooling_mode_sensor` | binary_sensor ID | True = cooling season |
| `alarm_sensor` | binary_sensor ID | Alarm monitoring |

**External Actuators (write):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `dehumidifier_switch` | switch ID | Controls dehumidifier hardware |
| `integration_switch` | switch ID | Controls integration (cooling) hardware |
| `fan_speed_number` | number ID | Fan speed output (0-100%) |

**Configuration Entities (Home Assistant):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_fan_speed_entity` | HA entity | Minimum fan speed (%) |
| `escalation_threshold_entity` | HA entity | Fan speed threshold for escalation (%) |
| `deescalation_threshold_entity` | HA entity | Fan speed threshold for de-escalation (%) |
| `escalation_delay_entity` | HA entity | Minutes before escalation triggers |
| `deescalation_delay_entity` | HA entity | Minutes before de-escalation triggers |

## Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `{component_id}_final_fan_speed` | sensor | Calculated fan speed (0-100%) |
| `{component_id}_automation_state` | text_sensor | Current state machine status |
| `{component_id}_humidity_state` | select | Humidity cascade state (Fan Only/Dehumidifying/Integration) |

## Usage Example

### Step 1: Create demand sensors externally

Use the [proportional demand sensor](proportional-demand.md) utility to create individual demand sensors, then aggregate with a MAX template:

```yaml
packages:
  co2_demand: !include
    file: packages/components/proportional_demand_sensor.yaml
    vars:
      component_id: "mev"
      component_name: "MEV"
      demand_slug: "co2"
      demand_name: "CO2"
      source_sensor_id: living_room_co2
      min_output_id: mev_min_fan_speed
      lower_bound_entity: "input_number.co2_lower_bound"
      upper_bound_entity: "input_number.co2_upper_bound"
      rate_multiplier: "0.05"

  humidity_demand: !include
    file: packages/components/proportional_demand_sensor.yaml
    vars:
      component_id: "mev"
      component_name: "MEV"
      demand_slug: "humidity"
      demand_name: "Humidity"
      source_sensor_id: bathroom_humidity
      min_output_id: mev_min_fan_speed
      lower_bound_entity: "input_number.humidity_lower_bound"
      upper_bound_entity: "input_number.humidity_upper_bound"
      rate_multiplier: "20.0"

sensor:
  - platform: template
    name: "MEV Max Demand"
    id: mev_max_demand
    unit_of_measurement: "%"
    lambda: |-
      float co2 = id(mev_co2_demand).state;
      float hum = id(mev_humidity_demand).state;
      if (isnan(co2)) co2 = 0;
      if (isnan(hum)) hum = 0;
      return std::max(co2, hum);
```

### Step 2: Create hardware entities externally

Define switches, alarm sensor, and fan speed number in your device or board config.

### Step 3: Include the controller

```yaml
packages:
  mev_ctrl: !include
    file: packages/coordinators/mev_ventilation.yaml
    vars:
      component_id: "mev"
      component_name: "MEV"
      # External sensors
      demand_sensor: mev_max_demand
      humidity_sensor: bathroom_humidity
      humidity_rate_sensor: mev_humidity_rate
      cooling_mode_sensor: summer_mode
      # External actuators
      dehumidifier_switch: mev_dehumidifier
      integration_switch: mev_integration
      alarm_sensor: mev_alarm
      fan_speed_number: mev_fan_speed
      # HA configuration
      min_fan_speed_entity: "input_number.mev_min_fan_speed"
      escalation_threshold_entity: "input_number.mev_escalation_threshold"
      deescalation_threshold_entity: "input_number.mev_deescalation_threshold"
      escalation_delay_entity: "input_number.mev_escalation_delay"
      deescalation_delay_entity: "input_number.mev_deescalation_delay"
      humidity_lower_sensor: mev_humidity_lower
```

### Required Home Assistant Helpers

Create these `input_number` helpers in Home Assistant (Settings > Devices > Helpers):

| Helper | Suggested Range | Suggested Default | Purpose |
|--------|----------------|-------------------|---------|
| Min fan speed | 0-100 | 20 | Minimum fan speed (%) |
| Escalation threshold | 0-100 | 70 | Fan speed that triggers escalation |
| De-escalation threshold | 0-100 | 40 | Fan speed below which de-escalation starts |
| Escalation delay | 1-60 | 10 | Minutes before escalating |
| De-escalation delay | 1-60 | 15 | Minutes before de-escalating |

## Integration Tips

- **Flexible demands**: Use any number of demand sensors. Aggregate them with a MAX template sensor and pass the result as `demand_sensor`. You can use 1 demand (humidity only) or 10 (one per room) - the controller doesn't care.
- **Hardware freedom**: The controller works with any switch/number entities. Use relay wrappers, Modbus outputs, GPIO, or virtual entities - as long as they implement the ESPHome switch/number interface.
- **Sensor aggregation**: If monitoring multiple rooms, create a `max` template sensor that takes the worst reading across all rooms, then feed that as the humidity/demand source.
- **Tuning**: Start with conservative values (high escalation threshold, long delays). Monitor the `automation_state` diagnostic sensor to understand system behavior before tightening thresholds.
- **Season transitions**: When `cooling_mode_sensor` goes false, any active Integration state automatically de-escalates to Dehumidifying on the next evaluation cycle.
