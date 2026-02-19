# Proportional Demand Sensor

Convert any sensor reading into a 0-100% demand signal with configurable bounds and optional rate-of-change boost.

## What It Does

The proportional demand sensor maps a sensor value (e.g., humidity, CO2, IAQ index) into a demand percentage between 0% and 100%. This demand signal can then drive fan speeds, valve positions, or other actuators proportionally. An optional rate-of-change boost increases demand when values are rising quickly, enabling proactive response before conditions deteriorate.

## How It Works

### Linear Mapping with Clamping

The core algorithm performs a linear interpolation between configurable lower and upper bounds:

```
position = (sensor_value - lower_bound) / (upper_bound - lower_bound)
position = clamp(position, 0.0, 1.0)
demand = min_output + (position * (100 - min_output))
```

- Below the lower bound: demand = minimum output (not zero - maintains baseline)
- At the upper bound: demand = 100%
- Between bounds: linear interpolation
- The `min_output` ensures the actuator never drops below a configurable minimum (e.g., minimum fan speed)

### Rate Boost (Optional)

When `rate_multiplier` is greater than 0, the sensor's rate of change per minute is multiplied and added to the base demand:

```
boost = max(0, rate_of_change * rate_multiplier)
total_demand = min(100, base_demand + boost)
```

- Only positive rates contribute (rising values increase demand; falling values don't reduce it below base)
- Rate is calculated by the included trend sensor using a sliding window moving average
- Set `rate_multiplier: "0.0"` (default) to disable rate boost entirely

### Error Handling

If any input is NaN or bounds are invalid (upper <= lower), the sensor returns the `fallback_value` (default: 20%) to maintain safe minimum operation.

## Dependencies

This component **automatically includes** `trend_sensor.yaml` from the same directory. You do not need to include it separately. The trend sensor provides rate-of-change data used by the optional rate boost feature.

**Dependency chain:**
```
proportional_demand_sensor.yaml
└── trend_sensor.yaml (auto-included)
```

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `component_id` | string | Yes | - | Prefix for entity IDs (e.g., `ventilation`) |
| `component_name` | string | Yes | - | Friendly name prefix (e.g., `Ventilation`) |
| `demand_slug` | string | Yes | - | Short name for demand type (e.g., `humidity`, `co2`) |
| `demand_name` | string | Yes | - | Friendly name for demand type (e.g., `Humidity`) |
| `source_sensor_id` | string | Yes | - | ID of the sensor to monitor |
| `min_output_id` | string | Yes | - | ID of a sensor providing the minimum output threshold |
| `lower_bound_entity` | string | Yes | - | HA entity ID for the lower bound (e.g., `input_number.humidity_lower`) |
| `upper_bound_entity` | string | Yes | - | HA entity ID for the upper bound (e.g., `input_number.humidity_upper`) |
| `rate_multiplier` | float | No | `0.0` | Multiplier for rate boost (0 = disabled) |
| `window_size` | int | No | `15` | Smoothing window for the trend sensor |
| `unit_of_measurement` | string | No | `%` | Output unit |
| `icon` | string | No | `mdi:gauge` | MDI icon |
| `accuracy_decimals` | int | No | `0` | Decimal precision for displayed value |
| `fallback_value` | float | No | `20.0` | Value returned when inputs are invalid |

**Exposed entities:**
- `sensor.{component_id}_{demand_slug}_demand` - Calculated demand percentage (0-100%)
- `sensor.{component_id}_{demand_slug}_rate` - Rate of change per minute (via trend sensor)

## Usage Examples

### Humidity Demand for Ventilation

```yaml
# Define the source sensor and minimum speed threshold
sensor:
  - platform: homeassistant
    id: bathroom_humidity
    entity_id: sensor.bathroom_humidity

  - platform: homeassistant
    id: ventilation_min_speed
    entity_id: input_number.ventilation_min_speed

# Include the proportional demand sensor
packages:
  humidity_demand: !include
    file: packages/components/proportional_demand_sensor.yaml
    vars:
      component_id: "ventilation"
      component_name: "Ventilation"
      demand_slug: "humidity"
      demand_name: "Humidity"
      source_sensor_id: bathroom_humidity
      min_output_id: ventilation_min_speed
      lower_bound_entity: "input_number.humidity_lower_bound"
      upper_bound_entity: "input_number.humidity_upper_bound"
      rate_multiplier: "5.0"
```

With this configuration:
- Lower bound = 50% RH, Upper bound = 70% RH, Min speed = 30%
- At 50% RH: demand = 30% (minimum)
- At 60% RH: demand = 65% (midpoint)
- At 70% RH: demand = 100%
- If humidity is rising at 2%/min with `rate_multiplier: 5.0`: boost = +10%

### CO2 Demand

```yaml
sensor:
  - platform: homeassistant
    id: living_room_co2
    entity_id: sensor.living_room_co2

  - platform: homeassistant
    id: ventilation_min_speed
    entity_id: input_number.ventilation_min_speed

packages:
  co2_demand: !include
    file: packages/components/proportional_demand_sensor.yaml
    vars:
      component_id: "ventilation"
      component_name: "Ventilation"
      demand_slug: "co2"
      demand_name: "CO2"
      source_sensor_id: living_room_co2
      min_output_id: ventilation_min_speed
      lower_bound_entity: "input_number.co2_lower_bound"
      upper_bound_entity: "input_number.co2_upper_bound"
      unit_of_measurement: "ppm"
```

### GitHub Remote Include

```yaml
packages:
  humidity_demand:
    url: github://your-username/vesta-climate-framework
    file: packages/components/proportional_demand_sensor.yaml
    vars:
      component_id: "mev"
      component_name: "MEV"
      demand_slug: "humidity"
      demand_name: "Humidity"
      source_sensor_id: bathroom_humidity
      min_output_id: mev_min_speed
      lower_bound_entity: "input_number.mev_humidity_lower"
      upper_bound_entity: "input_number.mev_humidity_upper"
      rate_multiplier: "3.0"
```

## Integration Tips

- **Multiple demands**: Include this package once per demand type. A ventilation coordinator can then take the MAX of all demand signals to drive a single fan speed
- **Bounds via HA**: The lower and upper bounds are read from Home Assistant `input_number` entities, allowing runtime adjustment from the HA dashboard without reflashing
- **Min output sensor**: The `min_output_id` should reference a sensor that provides the minimum acceptable output (e.g., minimum fan speed). This can be a constant template sensor or an HA input_number for runtime adjustment
- **Rate boost tuning**: Start with `rate_multiplier: "0.0"` (disabled). Enable it for demands where rapid changes need proactive response (e.g., humidity after shower). A value of 3-5 works well for humidity; CO2 typically doesn't need rate boost
- **Update interval**: The demand sensor updates every 60 seconds by default. The internal trend sensor updates more frequently (based on its own `update_interval`) to build accurate rate data
- **Downstream consumers**: Components like the MEV Ventilation Coordinator use multiple proportional demand sensors and select the highest demand (MAX aggregation) to drive fan speed
