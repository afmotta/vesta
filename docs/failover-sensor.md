# Failover Sensor

3-tier sensor failover with automatic recovery for reliable climate control.

## What It Does

The failover sensor monitors two sensor sources and automatically selects the best available one. If the primary source fails (returns NAN), it falls over to the secondary. If both fail, it enters Emergency mode (returns NAN), which downstream components can use to trigger safe shutdown procedures.

When a higher-priority sensor recovers, the failover sensor automatically switches back. All tier transitions are logged for diagnostics.

## How It Works

```
┌─────────────────────────────────────────────┐
│ Failover Sensor (output to PID / consumers) │
└──────────────┬──────────────────────────────┘
               │
   ┌───────────┼───────────┐
   │           │           │
   ▼           ▼           ▼
Tier 1      Tier 2      Tier 3
Primary     Secondary   Emergency
(preferred) (fallback)  (NAN output)
```

**Priority table:**

| Primary | Secondary | Active Tier | Output Value |
|---------|-----------|-------------|--------------|
| Valid   | Valid     | Primary     | Primary      |
| Valid   | NaN      | Primary     | Primary      |
| NaN     | Valid     | Secondary   | Secondary    |
| NaN     | NaN      | Emergency   | NaN          |

**Typical sensor source pairing:**
- Primary: Home Assistant sensor (proven, fast updates)
- Secondary: UDP/Modbus direct sensor (local, no HA dependency)
- Emergency: NAN triggers downstream safety logic (e.g., shutdown after timeout)

## Automatic Recovery

Recovery is automatic and immediate:
- When a higher-priority sensor starts reporting valid values again, the failover sensor switches back on the next update cycle
- Tier transitions are logged at INFO level (failover/recovery) or ERROR level (emergency)
- The `{sensor_id}_sensor_tier` text sensor always shows the current active tier for dashboard display

**Log examples:**
```
[failover] [living_room_temp] Failover: Primary → Secondary (primary sensor unavailable)
[failover] [living_room_temp] Recovery: Secondary → Primary (primary sensor restored)
[failover] [living_room_temp] Failover: Secondary → Emergency (all sensors unavailable)
```

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sensor_id` | string | Yes | - | Entity ID for the abstracted output sensor |
| `sensor_name` | string | Yes | - | Friendly name shown in Home Assistant |
| `unit_of_measurement` | string | Yes | - | Output unit (e.g., `°C`, `%`) |
| `device_class` | string | Yes | - | HA device class (e.g., `temperature`, `humidity`) |
| `primary_sensor` | string | Yes | - | ID of the primary sensor source |
| `secondary_sensor` | string | Yes | - | ID of the secondary/fallback sensor source |
| `internal` | bool | No | `true` | If `true`, hides the value sensor from HA (tier sensor always visible) |
| `accuracy_decimals` | int | No | `1` | Decimal precision for displayed value |
| `update_interval` | string | No | `10s` | How often to evaluate failover logic |

**Exposed entities:**
- `sensor.{sensor_id}` - The abstracted sensor value from the active tier
- `text_sensor.{sensor_id}_sensor_tier` - Current active tier name (`Primary`, `Secondary`, or `Emergency`)

## Usage Example

### Temperature Failover (HA + UDP)

```yaml
# First, define your sensor sources
sensor:
  - platform: homeassistant
    id: ha_living_room_temp
    entity_id: sensor.living_room_temperature

  - platform: udp
    id: udp_living_room_temp
    # ... UDP sensor config

# Then include the failover package
packages:
  temp_failover: !include
    file: packages/utils/failover_sensor.yaml
    vars:
      sensor_id: "living_room_temp"
      sensor_name: "Living Room Temperature"
      unit_of_measurement: "°C"
      device_class: "temperature"
      primary_sensor: ha_living_room_temp
      secondary_sensor: udp_living_room_temp
```

### Humidity Failover

```yaml
packages:
  humidity_failover: !include
    file: packages/utils/failover_sensor.yaml
    vars:
      sensor_id: "living_room_humidity"
      sensor_name: "Living Room Humidity"
      unit_of_measurement: "%"
      device_class: "humidity"
      primary_sensor: ha_living_room_humidity
      secondary_sensor: udp_living_room_humidity
```

### GitHub Remote Include

```yaml
packages:
  failover:
    url: github://your-username/vesta-climate-framework
    file: packages/utils/failover_sensor.yaml
    vars:
      sensor_id: "room_temp"
      sensor_name: "Room Temperature"
      unit_of_measurement: "°C"
      device_class: "temperature"
      primary_sensor: ha_room_temp
      secondary_sensor: modbus_room_temp
```

## Integration Tips

- **PID controllers** should consume the failover sensor output (`sensor_id`) rather than raw sensor sources directly
- **Emergency handling**: When the failover sensor outputs NAN, downstream PID controllers will stop actuating. Combine with a timeout-based shutdown script for safety
- **Multiple instances**: Include this package once per sensor that needs failover protection (temperature, humidity, etc.)
- **Sensor sources**: The primary and secondary sensors can be any ESPHome sensor - Home Assistant, UDP, Modbus, or even another template sensor
- **Update interval**: Match to your fastest sensor update rate. Default 10s works well for most climate control scenarios
