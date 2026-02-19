# Dew Point Sensor

Calculate dew point temperature from humidity and temperature sensors using the Magnus formula.

## What It Does

Creates a template sensor that continuously calculates the dew point temperature for a room. This is essential for radiant cooling systems: if the surface temperature of the radiant floor drops below the dew point, condensation occurs — damaging floors and creating slip hazards.

## How It Works

The [Magnus formula](https://en.wikipedia.org/wiki/Clausius%E2%80%93Clapeyron_relation#Meteorology_and_climatology) approximation calculates dew point from relative humidity (RH%) and temperature (T°C):

```
H = ln(RH/100) + (17.62 × T) / (243.12 + T)
Dew Point = 243.12 × H / (17.62 - H)
```

Accuracy is approximately ±0.35°C for typical indoor conditions (0–60°C, 1–100% RH).

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `room_slug` | string | Yes | - | Room identifier for entity IDs |
| `room_name` | string | Yes | - | Display name |
| `humidity_sensor` | string | Yes | - | ID of the humidity sensor |
| `temperature_sensor` | string | Yes | - | ID of the temperature sensor |
| `update_interval` | duration | No | `30s` | Recalculation interval |
| `accuracy_decimals` | int | No | `0` | Decimal precision |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.${room_slug}_dew_point` | Sensor | Calculated dew point in °C |

## Usage Example

```yaml
packages:
  dew_point: !include
    file: packages/components/dew_point_sensor.yaml
    vars:
      room_slug: "living_room"
      room_name: "Living Room"
      humidity_sensor: living_room_humidity
      temperature_sensor: living_room_temp
```

## Integration Tips

- **Radiant cooling safety**: Compare the dew point with the radiant supply water temperature. If the supply is within 2°C of the dew point, reduce radiant output and increase fancoil boost.
- **Fancoil Boost Coordinator** uses humidity thresholds rather than dew point directly, but the dew point sensor provides useful diagnostics for monitoring condensation risk.
- **Default precision of 0 decimals** is appropriate because the formula itself has ±0.35°C uncertainty.
