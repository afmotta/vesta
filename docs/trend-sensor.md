# Trend Sensor

Rate-of-change calculator with sliding window smoothing for any ESPHome sensor.

## What It Does

The trend sensor monitors any numeric sensor and calculates how fast its value is changing per minute. This enables predictive logic: instead of reacting only to absolute values, downstream components can detect acceleration and respond before thresholds are breached.

Use cases include detecting rapid temperature drops (window opened), humidity spikes (shower running), or CO2 accumulation rates (room filling up).

## How It Works

1. On each sensor update, the lambda computes `(current_value - previous_value) / elapsed_minutes`
2. If the source sensor returns NAN (unavailable), the trend sensor also returns NAN
3. The first reading returns 0.0 (no previous value to compare against)
4. A `sliding_window_moving_average` filter smooths the output over `window_size` samples, reducing noise while preserving trend direction
5. Every smoothed value is published immediately (`send_every: 1`)

**Output units** match the source sensor's unit per minute. For example, a temperature sensor in °C produces a trend in °C/min. A positive value means increasing; negative means decreasing.

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sensor_id` | string | Yes | - | Entity ID for the created trend sensor |
| `source_sensor` | string | Yes | - | ID of the sensor to analyze |
| `unit_of_measurement` | string | Yes | - | Output unit (e.g., `°C/min`, `%/min`) |
| `sensor_name` | string | No | `"Trend Sensor"` | Friendly name shown in Home Assistant |
| `window_size` | int | No | `10` | Sliding window size (more = smoother, slower response) |
| `accuracy_decimals` | int | No | `2` | Decimal precision for displayed value |
| `icon` | string | No | `"mdi:trending-up"` | Material Design Icon |
| `internal` | bool | No | `false` | If `true`, hides sensor from Home Assistant |

## Usage Example

### Temperature Trend

```yaml
packages:
  temp_trend: !include
    file: packages/components/trend_sensor.yaml
    vars:
      sensor_id: "living_room_temp_trend"
      source_sensor: sensor.living_room_temperature
      unit_of_measurement: "°C/min"
      sensor_name: "Living Room Temperature Trend"
      window_size: "10"
```

### Humidity Trend

```yaml
packages:
  humidity_trend: !include
    file: packages/components/trend_sensor.yaml
    vars:
      sensor_id: "bathroom_humidity_trend"
      source_sensor: sensor.bathroom_humidity
      unit_of_measurement: "%/min"
      sensor_name: "Bathroom Humidity Trend"
      window_size: "15"
```

### GitHub Remote Include

```yaml
packages:
  trend:
    url: github://your-username/vesta-climate-framework
    file: packages/components/trend_sensor.yaml
    vars:
      sensor_id: "room_temp_trend"
      source_sensor: sensor.room_temperature
      unit_of_measurement: "°C/min"
```

## Integration Tips

- **Fancoil Boost Coordinator** uses the trend sensor to detect whether temperature is improving or stagnating under PID saturation (predictive boost trigger)
- **Proportional Demand Sensor** uses the trend sensor for optional rate-of-change boost on demand calculations
- **Window size trade-off**: Smaller values (5) react faster but are noisier; larger values (20) are smoother but add lag. Default of 10 is a good balance for climate control where sensor updates arrive every 30-60 seconds
- **Multiple instances**: You can include this package multiple times with different `sensor_id` values to track trends on different sensors simultaneously
