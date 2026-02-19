# Heat-Only Radiant

Heat-only radiant floor zone with PID control, slow PWM output, and manual override.

## What It Does

Creates a complete heat-only radiant floor zone. The PID controller reads your room temperature sensor, calculates the required heat output, and drives a slow PWM signal to a relay controlling the zone valve or pump. An override mechanism allows manual control for commissioning or special situations.

This is the base building block for `radiant.yaml` (dual heat+cool). Use this directly for zones that only need heating — second floors, attics, or systems without cooling capability.

## How It Works

```
Temperature Sensor → PID Controller → Override Logic → Slow PWM → Relay
                                           ↑
                                    Manual Override
                                   (switch + number)
```

1. PID reads temperature and calculates heat demand (0-100%)
2. A template output applies override logic: if override switch is ON, use override percentage; otherwise use PID output
3. Slow PWM converts the 0-100% signal to on/off cycles (default 60s period)
4. The relay opens/closes the zone valve accordingly
5. Seasonal mode integration: automatically switches PID to HEAT or OFF based on the seasonal mode coordinator

## Dependencies

- **pid.yaml** — Included automatically (which also includes pid_sensors.yaml)

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `room_slug` | string | Yes | - | Room identifier for entity IDs |
| `room_name` | string | Yes | - | Display name for the zone |
| `temperature_sensor` | string | Yes | - | Temperature sensor ID |
| `relay_id` | string | Yes | - | Switch ID for the zone valve relay |
| `seasonal_mode_id` | string | Yes | - | ID of the seasonal mode select entity |
| `pwm_period` | duration | No | `60s` | Slow PWM cycle period |
| `kp` | float | No | `0.8` | PID proportional gain |
| `ki` | float | No | `0.005` | PID integral gain |
| `kd` | float | No | `0.05` | PID derivative gain |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `climate.pid_radiant_${room_slug}` | Climate | PID controller |
| `switch.radiant_${room_slug}_override` | Switch | Enable/disable manual override |
| `number.radiant_${room_slug}_override_value` | Number | Manual override percentage (0-100%) |
| `output.radiant_output_${room_slug}` | Output | Template output (with override logic) |
| `output.radiant_pwm_${room_slug}` | Output | Slow PWM driving the relay |
| *(plus all PID diagnostic sensors)* | | |

## Usage Example

```yaml
packages:
  radiant: !include
    file: packages/components/heat_only_radiant.yaml
    vars:
      room_slug: "attic"
      room_name: "Attic"
      temperature_sensor: sensor.attic_temperature
      relay_id: relay_12
      seasonal_mode_id: hp_mode
```

## Integration Tips

- **Override mechanism**: Turn on the override switch and set a percentage to bypass PID. Useful for commissioning new zones or testing actuators.
- **PWM period**: 60 seconds works well for radiant floors with high thermal mass. Shorter periods (30s) for faster-response systems.
- **Seasonal mode**: The zone automatically turns OFF during COOL season. Use `radiant.yaml` instead if you need both heating and cooling.
