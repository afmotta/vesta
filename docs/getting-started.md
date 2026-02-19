# Getting Started

How to start using Vesta components in your ESPHome configuration.

## Prerequisites

- **ESPHome** 2025.12.0 or later
- **ESP32** board (ESP-IDF or Arduino framework)
- **Home Assistant** (optional, recommended for tuning parameters and monitoring)

No additional libraries or custom components are required. Vesta uses only standard ESPHome YAML features: `packages`, `!include`, substitutions, and `defaults`.

## Including Vesta Packages

### Option 1: Local Include

Copy the `packages/` directory into your ESPHome project, then reference components with `!include`:

```yaml
packages:
  my_trend: !include
    file: vesta/packages/components/trend_sensor.yaml
    vars:
      sensor_id: "room_temp_trend"
      source_sensor: room_temperature
      unit_of_measurement: "°C/min"
```

### Option 2: GitHub Remote Include

Reference packages directly from GitHub without downloading:

```yaml
packages:
  my_trend:
    url: github://your-username/vesta-climate-framework
    file: packages/components/trend_sensor.yaml
    vars:
      sensor_id: "room_temp_trend"
      source_sensor: room_temperature
      unit_of_measurement: "°C/min"
```

### Variable Passing

Every Vesta component declares its required and optional variables in a header comment block at the top of the file. Required variables have no defaults and must always be provided. Optional variables have sensible defaults defined in a `defaults:` block.

```yaml
# Example header showing required vs optional
# Required vars:
#   sensor_id            - must be provided
#   source_sensor        - must be provided
#
# Optional vars:
#   window_size          - default: 10
```

## Recommended Learning Path

Start with the simplest component and build up:

### Step 1: Trend Sensor

The [trend sensor](trend-sensor.md) is the smallest component (60 lines). It takes any numeric sensor and calculates rate of change per minute. This is a good first include to verify your setup works.

```yaml
packages:
  temp_trend: !include
    file: packages/components/trend_sensor.yaml
    vars:
      sensor_id: "my_temp_trend"
      source_sensor: my_temperature_sensor
      unit_of_measurement: "°C/min"
```

### Step 2: Failover Sensor

The [failover sensor](failover-sensor.md) adds reliability to any sensor by providing automatic fallback between two sources. If you have both HA and local (Modbus/UDP) sensor sources, this prevents PID controllers from losing their input.

```yaml
packages:
  temp_failover: !include
    file: packages/components/failover_sensor.yaml
    vars:
      sensor_id: "room_temp"
      sensor_name: "Room Temperature"
      unit_of_measurement: "°C"
      device_class: "temperature"
      primary_sensor: ha_room_temp
      secondary_sensor: local_room_temp
```

### Step 3: Proportional Demand Sensor

The [proportional demand sensor](proportional-demand.md) converts a raw sensor value (CO2 ppm, humidity %, IAQ index) into a 0-100% demand signal using configurable bounds. Useful for driving ventilation fan speed proportionally.

### Step 4: Coordinators

Once you're comfortable with the utilities, move to the coordinators:

- [Fancoil Boost Coordinator](fancoil-boost.md) - The flagship "Base + Boost" pattern for hybrid radiant + fancoil zones
- [MEV Ventilation Coordinator](mev-ventilation.md) - Multi-demand ventilation with humidity cascade state machine

## Component Dependency Map

```
radiant.yaml ──includes──▶ heat_only_radiant.yaml ──includes──▶ pid.yaml ──includes──▶ pid_sensors.yaml
fancoil.yaml ──includes──▶ pid.yaml
mixing_pump.yaml ──includes──▶ pid.yaml
fancoil_boost.yaml ──uses──▶ trend_sensor.yaml
proportional_demand_sensor.yaml ──uses──▶ trend_sensor.yaml
modbus_relay_board.yaml ──includes──▶ modbus_relay_switch.yaml (×8)
modbus_analog_outputs_board.yaml ──includes──▶ modbus_analog_output.yaml (×8)

Standalone: trend_sensor, failover_sensor, dew_point_sensor, direct_pump, seasonal_mode
```

Components include their dependencies automatically. You only need to include the top-level component.

## Complete Example

Two complete examples are available:

- [examples/two_zone_radiant_fancoil.yaml](../examples/two_zone_radiant_fancoil.yaml) - Two zones with radiant floor PID, fancoil boost, failover sensors, and trend analysis
- [examples/mev_two_demand.yaml](../examples/mev_two_demand.yaml) - MEV ventilation driven by humidity + CO2 proportional demand with humidity cascade state machine

## Component Reference

### Utility Components

| Component | Docs |
|-----------|------|
| Trend Sensor | [trend-sensor.md](trend-sensor.md) |
| Failover Sensor | [failover-sensor.md](failover-sensor.md) |
| Proportional Demand Sensor | [proportional-demand.md](proportional-demand.md) |
| Dew Point Sensor | [dew-point-sensor.md](dew-point-sensor.md) |

### Zone Components (PID Control)

| Component | Docs |
|-----------|------|
| PID Controller | [pid.md](pid.md) |
| PID Autotune | [pid-autotune.md](pid-autotune.md) |
| Heat-Only Radiant | [heat-only-radiant.md](heat-only-radiant.md) |
| Radiant (Heat + Cool) | [radiant.md](radiant.md) |
| Fancoil | [fancoil.md](fancoil.md) |

### Pump Components

| Component | Docs |
|-----------|------|
| Direct Pump | [direct-pump.md](direct-pump.md) |
| Mixing Pump | [mixing-pump.md](mixing-pump.md) |

### Coordinators

| Component | Docs |
|-----------|------|
| Seasonal Mode | [seasonal-mode.md](seasonal-mode.md) |
| Fancoil Boost | [fancoil-boost.md](fancoil-boost.md) |
| MEV Ventilation | [mev-ventilation.md](mev-ventilation.md) |

### Device Drivers

| Component | Docs |
|-----------|------|
| Modbus Relay Board | [modbus-relay-board.md](modbus-relay-board.md) |
| Modbus Analog Board | [modbus-analog-board.md](modbus-analog-board.md) |
