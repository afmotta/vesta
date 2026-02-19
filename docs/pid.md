# PID Controller

Production-tested PID climate controller wrapper with full diagnostic sensor exposure.

## What It Does

The PID package wraps ESPHome's `climate.pid` platform into a reusable, parameterized component. It creates a PID climate entity for proportional temperature control and automatically includes a full suite of diagnostic sensors (via `pid_sensors.yaml`) for monitoring PID internals.

Use this as the foundation for any zone that needs proportional control — radiant floors, fancoils, mixing valves, or any other actuator driven by temperature error.

## How It Works

1. A `climate.pid` entity is created with your specified gains (Kp, Ki, Kd)
2. The PID reads from your temperature sensor and calculates heat/cool output
3. Diagnostic sensors expose all PID internals: output result, error, proportional/integral/derivative terms, current gains, and active state binary sensors
4. Downstream components (radiant, fancoil) extend this climate entity to attach their specific outputs

## Dependencies

- **pid_sensors.yaml** — Included automatically. Creates 10 numeric sensors and 3 binary sensors for PID diagnostics.

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `circuit_slug` | string | Yes | - | Entity ID prefix (e.g., `"radiant_living_room"`) |
| `circuit_name` | string | Yes | - | Display name (e.g., `"Radiant Living Room"`) |
| `sensor` | string | Yes | - | Temperature sensor ID to track |
| `kp` | float | Yes | - | Proportional gain |
| `ki` | float | Yes | - | Integral gain |
| `kd` | float | Yes | - | Derivative gain |
| `default_target_temperature` | float | No | `20.00` | Initial setpoint in °C |
| `visual_min_temperature` | float | No | `15` | HA UI minimum temperature |
| `visual_max_temperature` | float | No | `35` | HA UI maximum temperature |
| `visual_temperature_step` | float | No | `0.1` | HA UI temperature step |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `climate.pid_${circuit_slug}` | Climate | PID controller |
| `sensor.pid_${circuit_slug}_result` | Sensor | PID output (-100% to 100%) |
| `sensor.pid_${circuit_slug}_error` | Sensor | Current error (setpoint - actual) |
| `sensor.pid_${circuit_slug}_heat` | Sensor | Heat output percentage |
| `sensor.pid_${circuit_slug}_cool` | Sensor | Cool output percentage |
| `sensor.pid_${circuit_slug}_proportional` | Sensor | P term contribution |
| `sensor.pid_${circuit_slug}_integral` | Sensor | I term contribution |
| `sensor.pid_${circuit_slug}_derivative` | Sensor | D term contribution |
| `sensor.pid_${circuit_slug}_kp` | Sensor | Current Kp value |
| `sensor.pid_${circuit_slug}_ki` | Sensor | Current Ki value |
| `sensor.pid_${circuit_slug}_kd` | Sensor | Current Kd value |
| `binary_sensor.pid_${circuit_slug}_is_active` | Binary | PID actively controlling |
| `binary_sensor.pid_${circuit_slug}_is_heating` | Binary | Currently in heat mode |
| `binary_sensor.pid_${circuit_slug}_is_cooling` | Binary | Currently in cool mode |

## Usage Example

```yaml
packages:
  pid: !include
    file: packages/components/pid.yaml
    vars:
      circuit_slug: "radiant_living_room"
      circuit_name: "Radiant Living Room"
      sensor: sensor.living_room_temperature
      kp: 0.8
      ki: 0.005
      kd: 0.05
```

### PID Tuning Guidelines

| System Type | Kp | Ki | Kd | Notes |
|-------------|----|----|-----|-------|
| Radiant floor (slow) | 0.5–1.0 | 0.001–0.01 | 0.01–0.1 | High thermal inertia |
| Fancoil (fast) | 0.2–0.5 | 0.005–0.02 | 0.01–0.05 | Fast air response |
| Mixing valve | 0.2 | 0.01 | 0.0 | Moderate response |

## Integration Tips

- **Radiant zones** include this automatically — you don't need to include `pid.yaml` separately when using `radiant.yaml` or `heat_only_radiant.yaml`
- **Fancoil zones** also include PID automatically via `fancoil.yaml`
- The `is_heating` / `is_cooling` binary sensors are used by the **Seasonal Mode Coordinator** for demand-driven mode transitions
- Use **PID Autotune** to find optimal gains for your specific system
