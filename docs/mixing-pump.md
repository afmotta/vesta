# Mixing Pump

Mixing valve + circulation pump control with PID-driven valve position and Dallas temperature sensor.

## What It Does

Controls a mixing valve assembly that blends hot supply water with cooler return water to achieve a target supply temperature. A Dallas 1-Wire temperature sensor monitors the mixed supply temperature, a PID controller adjusts the valve position, and a binary sensor trigger controls the circulation pump relay.

## How It Works

```
Dallas Temp Sensor → PID Controller → Valve Output (0-100%)
                                          ↓
Binary Trigger → Pump Relay ON/OFF    Mixing Valve Position
```

1. Dallas sensor reads the mixed supply water temperature
2. PID calculates valve position to reach target temperature
3. PID output drives the mixing valve actuator (heat and cool outputs both connected)
4. A separate binary sensor trigger turns the circulation pump on/off

## Dependencies

- **pid.yaml** — Included automatically (which includes pid_sensors.yaml)

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `area_slug` | string | Yes | - | Area identifier for entity IDs (e.g., `"ground_floor"`) |
| `area_name` | string | Yes | - | Display name (e.g., `"Ground Floor"`) |
| `dallas_address` | string | Yes | - | Dallas sensor address (e.g., `"0x01234567890ABCDE"`) |
| `one_wire_bus_id` | string | Yes | - | 1-Wire bus ID (e.g., `"one_wire_01"`) |
| `output_id` | string | Yes | - | Output entity for mixing valve actuator |
| `sensor_id` | string | Yes | - | Binary sensor ID that triggers pump on/off |
| `relay_id` | string | Yes | - | Switch ID for the circulation pump relay |
| `kp` | float | No | `0.2` | PID proportional gain |
| `ki` | float | No | `0.01` | PID integral gain |
| `kd` | float | No | `0.0` | PID derivative gain |
| `valve_slug` | string | No | `"mixing_valve_${area_slug}"` | Valve entity slug |
| `valve_name` | string | No | `"Mixing Valve for ${area_name}"` | Valve display name |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.dallas_${dallas_address}` | Sensor | Supply water temperature |
| `climate.pid_${valve_slug}` | Climate | PID controller for valve position |
| `binary_sensor.${sensor_id}_wrapped` | Binary (internal) | Pump trigger wrapper |
| *(plus all PID diagnostic sensors)* | | |

## Usage Example

```yaml
packages:
  mixing: !include
    file: packages/components/mixing_pump.yaml
    vars:
      area_slug: "ground_floor"
      area_name: "Ground Floor"
      dallas_address: "0x01234567890ABCDE"
      one_wire_bus_id: "one_wire_01"
      output_id: mixing_valve_output
      sensor_id: ground_floor_demand
      relay_id: relay_13
```

## Integration Tips

- **Dallas address**: Find your sensor's address from the ESPHome logs on first boot. Each Dallas sensor has a unique 64-bit address.
- **PID gains**: Default Kd=0.0 works well for mixing valves which have moderate response time. Derivative is often unnecessary.
- **Valve actuator**: The `output_id` connects to whatever drives the mixing valve — typically a 0-10V analog output via Modbus.
