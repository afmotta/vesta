# MEV Ventilation Coordinator

Multi-demand mechanical extract ventilation with humidity cascade state machine and automatic mode escalation.

## What It Does

The MEV coordinator drives a mechanical extract ventilation unit based on three air quality demands (CO2, IAQ, humidity). It calculates each demand as a percentage, takes the highest (MAX aggregation), and outputs that as the fan speed. A separate humidity cascade state machine automatically escalates through Fan Only, Dehumidifying, and Cooling modes based on sustained humidity conditions.

## How It Works

### Multi-Demand Orchestration

Three independent proportional demand sensors each convert their input into a 0-100% demand signal:

```
CO2 Sensor ──▶ CO2 Demand (0-100%)    ──┐
                                          │
IAQ Sensor ──▶ IAQ Demand (0-100%)    ──┼──▶ MAX ──▶ Final Fan Speed
                                          │
Humidity   ──▶ Humidity Demand (0-100%)──┘
```

**MAX aggregation**: The highest demand wins. If CO2 demands 40%, IAQ demands 25%, and humidity demands 70%, the fan runs at 70%. This ensures the worst air quality dimension always gets addressed.

Each demand sensor uses configurable lower/upper bounds (set via Home Assistant `input_number` entities) and optional rate-of-change boost for proactive response.

A **dominant demand** diagnostic sensor reports which demand is currently driving the fan speed.

### Humidity Cascade State Machine

Independent of fan speed, the coordinator manages a 3-state machine for humidity control hardware:

```
┌──────────┐    escalate     ┌───────────────┐    escalate     ┌─────────┐
│ Fan Only │ ──────────────▶ │ Dehumidifying  │ ──────────────▶ │ Cooling │
│          │ ◀────────────── │               │ ◀────────────── │         │
└──────────┘   de-escalate   └───────────────┘   de-escalate   └─────────┘
```

| State | Hardware | Description |
|-------|----------|-------------|
| **Fan Only** | Fan running, dehumidifier OFF, cooling OFF | Normal ventilation |
| **Dehumidifying** | Fan running, dehumidifier ON, cooling OFF | Active moisture removal |
| **Cooling** | Fan running, dehumidifier ON, cooling ON | Maximum humidity reduction (summer only) |

### Escalation Rules

Escalation occurs when **both** conditions are sustained for the configured delay:
1. Final fan speed >= escalation threshold
2. Humidity rate of change > 0 (humidity is rising)

**Fan Only → Dehumidifying**: Always available when conditions are met.

**Dehumidifying → Cooling**: Only available during cooling season (`cooling_mode_sensor` is true). This prevents energy-wasting cooling in winter.

### De-escalation Rules

De-escalation occurs when **both** conditions are sustained for the configured delay:
1. Humidity < lower bound (below the demand range)
2. Final fan speed < de-escalation threshold

**Cooling → Dehumidifying**: Also triggers immediately when cooling season ends.

**Dehumidifying → Fan Only**: Only when not simultaneously escalating (prevents flapping).

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

If the alarm input activates, the fan speed is immediately set to 0% and an ERROR-level log is emitted. Normal operation resumes when the alarm clears.

## Dependencies

This component includes 3 proportional demand sensors, each of which includes a trend sensor:

```
mev_ventilation.yaml (packages/coordinators/)
├── proportional_demand_sensor.yaml × 3 (packages/utils/)
│   └── trend_sensor.yaml × 3 (packages/utils/)
```

All dependencies are auto-included. You only need to include `mev_ventilation.yaml`.

## Parameter Reference

### Required Parameters

**Identity:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_id` | string | Prefix for entity IDs (e.g., `mev`) |
| `component_name` | string | Friendly name prefix (e.g., `MEV`) |

**Hardware:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `power_relay` | ID | Relay for main power |
| `mode_relay` | ID | Relay for winter/summer mode |
| `dehumidifier_relay` | ID | Relay for dehumidifier |
| `cooling_relay` | ID | Relay for cooling integration |
| `fan_speed_output` | ID | DAC output for 0-10V fan speed |
| `alarm_input` | ID | Binary sensor for alarm monitoring |

**Sensor Sources:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `humidity_sensor` | ID | Humidity sensor to monitor |
| `co2_sensor` | ID | CO2 sensor to monitor |
| `iaq_sensor` | ID | IAQ (air quality index) sensor to monitor |
| `cooling_mode_sensor` | ID | Binary sensor: true = cooling season |

**Configuration Entities (Home Assistant):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_fan_speed_entity` | HA entity | Minimum fan speed (%) |
| `escalation_threshold_entity` | HA entity | Fan speed threshold for escalation (%) |
| `deescalation_threshold_entity` | HA entity | Fan speed threshold for de-escalation (%) |
| `escalation_delay_entity` | HA entity | Minutes before escalation triggers |
| `deescalation_delay_entity` | HA entity | Minutes before de-escalation triggers |

**Demand Sensor Bounds (Home Assistant):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `co2_lower_bound_entity` | HA entity | CO2 lower bound for demand calculation |
| `co2_upper_bound_entity` | HA entity | CO2 upper bound for demand calculation |
| `iaq_lower_bound_entity` | HA entity | IAQ lower bound for demand calculation |
| `iaq_upper_bound_entity` | HA entity | IAQ upper bound for demand calculation |
| `humidity_lower_bound_entity` | HA entity | Humidity lower bound for demand calculation |
| `humidity_upper_bound_entity` | HA entity | Humidity upper bound for demand calculation |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `co2_rate_multiplier` | float | `0.05` | Rate boost multiplier for CO2 demand |
| `iaq_rate_multiplier` | float | `2.0` | Rate boost multiplier for IAQ demand |
| `humidity_rate_multiplier` | float | `20.0` | Rate boost multiplier for humidity demand |

## Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `{component_id}_final_fan_speed` | sensor | Calculated fan speed (0-100%) |
| `{component_id}_co2_demand` | sensor | CO2 demand percentage |
| `{component_id}_iaq_demand` | sensor | IAQ demand percentage |
| `{component_id}_humidity_demand` | sensor | Humidity demand percentage |
| `{component_id}_dominant_demand` | text_sensor | Which demand drives fan speed |
| `{component_id}_automation_state` | text_sensor | Current state machine status |
| `{component_id}_humidity_state` | select | Humidity cascade state (Fan Only/Dehumidifying/Cooling) |
| `{component_id}_fan_speed` | number | Fan speed control slider (0-100%) |
| `{component_id}_power` | switch | Main power |
| `{component_id}_mode` | switch | Winter/Summer mode |
| `{component_id}_dehumidifier` | switch | Dehumidifier |
| `{component_id}_cooling` | switch | Cooling integration |
| `{component_id}_alarm` | binary_sensor | Alarm status |

## Usage Example

```yaml
packages:
  mev: !include
    file: packages/coordinators/mev_ventilation.yaml
    vars:
      component_id: "mev"
      component_name: "MEV"
      # Hardware
      power_relay: relay_1
      mode_relay: relay_2
      dehumidifier_relay: relay_3
      cooling_relay: relay_4
      fan_speed_output: dac_1
      alarm_input: input_1
      # Sensor sources
      humidity_sensor: bathroom_humidity
      co2_sensor: living_room_co2
      iaq_sensor: living_room_iaq
      cooling_mode_sensor: summer_mode
      # HA configuration entities
      min_fan_speed_entity: "input_number.mev_min_fan_speed"
      escalation_threshold_entity: "input_number.mev_escalation_threshold"
      deescalation_threshold_entity: "input_number.mev_deescalation_threshold"
      escalation_delay_entity: "input_number.mev_escalation_delay"
      deescalation_delay_entity: "input_number.mev_deescalation_delay"
      # Demand sensor bounds
      co2_lower_bound_entity: "input_number.co2_lower_bound"
      co2_upper_bound_entity: "input_number.co2_upper_bound"
      iaq_lower_bound_entity: "input_number.iaq_lower_bound"
      iaq_upper_bound_entity: "input_number.iaq_upper_bound"
      humidity_lower_bound_entity: "input_number.humidity_lower_bound"
      humidity_upper_bound_entity: "input_number.humidity_upper_bound"
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
| CO2 lower/upper bound | 400-2000 | 600/1000 | PPM range for demand calculation |
| IAQ lower/upper bound | 0-500 | 50/150 | IAQ index range for demand calculation |
| Humidity lower/upper bound | 0-100 | 50/70 | % RH range for demand calculation |

## Integration Tips

- **Sensor aggregation**: If monitoring multiple rooms, create a `max` template sensor that takes the worst reading across all rooms, then feed that as the CO2/IAQ/humidity source
- **Hardware abstraction**: The relay switches wrap raw relay entities (e.g., PCF8574 GPIO expanders) with proper state tracking and friendly names
- **Fan speed mapping**: The 0-100% fan speed maps linearly to 0-10V via the DAC output. Adjust your MEV unit's configuration if it uses a different voltage range
- **Alarm handling**: The alarm input is typically a normally-closed contact. When the circuit opens (alarm), fan speed drops to 0% immediately
- **Tuning**: Start with conservative values (high escalation threshold, long delays). Monitor the `automation_state` and `dominant_demand` diagnostic sensors to understand system behavior before tightening thresholds
- **Season transitions**: When `cooling_mode_sensor` goes false, any active Cooling state automatically de-escalates to Dehumidifying on the next evaluation cycle
