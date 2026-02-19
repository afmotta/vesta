# Radiant

Dual-mode radiant floor zone supporting both heating and cooling with PID control.

## What It Does

Extends `heat_only_radiant.yaml` with cooling support. The same PID controller, override mechanism, and slow PWM output are used, but the zone now responds to HEAT, COOL, and OFF seasonal modes.

Use this for zones with reversible radiant floor systems (e.g., heat pump with changeover valve).

## How It Works

Builds on heat-only radiant by:
1. Adding `cool_output` to the PID climate entity (same physical output — the heat pump changeover valve handles the fluid temperature)
2. Overriding the seasonal mode handler to support three states: HEAT → PID heat mode, COOL → PID cool mode, anything else → PID off

## Dependencies

- **heat_only_radiant.yaml** — Included automatically (which includes pid.yaml → pid_sensors.yaml)

## Parameter Reference

Same parameters as [Heat-Only Radiant](heat-only-radiant.md). No additional parameters.

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

## Usage Example

```yaml
packages:
  radiant: !include
    file: packages/components/radiant.yaml
    vars:
      room_slug: "living_room"
      room_name: "Living Room"
      temperature_sensor: sensor.living_room_temperature
      relay_id: relay_1
      seasonal_mode_id: hp_mode
```

## Integration Tips

- **Cooling mode PID gains**: You may want higher gains for cooling than heating. Currently both modes share the same Kp/Ki/Kd. Override gains at the device level if needed.
- **Dew point protection**: When using radiant cooling, pair with `dew_point_sensor.yaml` and the Fancoil Boost Coordinator to prevent condensation.
- **Fancoil boost**: Combine with `fancoil.yaml` and the Fancoil Boost Coordinator for hybrid radiant+fancoil zones.
