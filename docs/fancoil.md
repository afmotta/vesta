# Fancoil

Fancoil unit zone with PID control for 0-10V analog speed output.

## What It Does

Creates a PID-controlled fancoil zone. The PID reads room temperature and outputs a proportional signal (0.0–1.0) to a template output, which is typically connected to a Modbus analog output for 0-10V fan speed control.

Fancoils respond much faster than radiant floors, so the default PID gains are tuned for quicker response with less overshoot.

## How It Works

```
Temperature Sensor → PID Controller → Float Output (0.0-1.0) → Analog Output (0-10V)
```

1. PID reads temperature and calculates demand
2. In HEAT mode, heat output drives the fan; in COOL mode, cool output drives it
3. Seasonal mode integration: switches PID between HEAT, COOL, and OFF automatically
4. The output connects to a Modbus analog output or any ESPHome `output` platform

## Dependencies

- **pid.yaml** — Included automatically (which includes pid_sensors.yaml)

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `room_slug` | string | Yes | - | Room identifier for entity IDs |
| `room_name` | string | Yes | - | Display name for the zone |
| `temperature_sensor` | string | Yes | - | Temperature sensor ID |
| `output_id` | string | Yes | - | Output entity for fan speed control |
| `seasonal_mode_id` | string | Yes | - | ID of the seasonal mode select entity |
| `kp` | float | No | `0.2` | PID proportional gain (lower than radiant) |
| `ki` | float | No | `0.01` | PID integral gain |
| `kd` | float | No | `0.05` | PID derivative gain |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `climate.pid_fancoil_${room_slug}` | Climate | PID controller |
| *(plus all PID diagnostic sensors)* | | |

## Usage Example

```yaml
packages:
  fancoil: !include
    file: packages/components/fancoil.yaml
    vars:
      room_slug: "living_room"
      room_name: "Living Room"
      temperature_sensor: sensor.living_room_temperature
      output_id: fancoil_living_room_output
      seasonal_mode_id: hp_mode
```

## Integration Tips

- **Output connection**: The `output_id` typically references a Modbus analog output entity. See [Modbus Analog Board](modbus-analog-board.md) for creating 0-10V outputs.
- **Fancoil Boost**: For hybrid radiant+fancoil zones, use the Fancoil Boost Coordinator instead of a standalone fancoil. The coordinator manages when the fancoil activates as a supplement to radiant.
- **Lower gains**: Default Kp (0.2) is much lower than radiant (0.8) because fancoils respond in minutes rather than hours.
