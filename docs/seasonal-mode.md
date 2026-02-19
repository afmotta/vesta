# Seasonal Mode Coordinator

Three-tier seasonal mode selection that automatically manages HEAT/COOL/SANITARY_ONLY transitions.

## What It Does

The seasonal mode coordinator is the central decision-maker for your entire HVAC system's operating mode. It determines whether the system should be heating, cooling, or in standby (sanitary hot water only). All zone components (radiant, fancoil) subscribe to this coordinator and automatically switch their PID mode when the season changes.

## How It Works

Three decision tiers, evaluated every minute:

### Tier 1: Calendar Gates (Hard Locks)

During defined calendar periods, the mode is locked regardless of demand:

```
Oct 15 ──────────────── Apr 15    → HEAT (Winter Lock)
Jun 1  ──────────────── Aug 31    → COOL (Summer Lock)
Apr 15 ── May 31                  → Spring Shoulder
Sep 1  ── Oct 14                  → Autumn Shoulder
```

All dates are configurable via optional parameters.

### Tier 2: Weather Intelligence

Placeholder for future weather API integration (not yet implemented).

### Tier 3: Demand-Driven Transitions (Shoulder Seasons)

During shoulder seasons (spring and autumn), mode transitions are driven by PID demand:

- If **any zone PID requests heat** → switch to HEAT
- If **any zone PID requests cool** → switch to COOL
- At shoulder season entry → reset to SANITARY_ONLY

This lets the system respond to actual conditions during transitional periods.

## Architecture

```
┌─────────────────────────────────────┐
│        Seasonal Mode Select         │
│  (HEAT / COOL / SANITARY_ONLY)      │
├─────────────────────────────────────┤
│  Calendar Gates → Hard lock mode    │
│  Demand Signals → Shoulder mode     │
├─────────────────────────────────────┤
│         ↓ on_value event ↓          │
├──────┬──────┬──────┬────────────────┤
│ Zone │ Zone │ Zone │   ...          │
│  1   │  2   │  3   │               │
└──────┴──────┴──────┴────────────────┘
```

Zone components extend the select entity's `on_value` trigger to react to mode changes.

## Parameter Reference

### Required Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `seasonal_mode_id` | string | Yes | - | ID for the select entity |
| `seasonal_mode_name` | string | Yes | - | Display name in Home Assistant |
| `time_id` | string | Yes | - | ESPHome time source ID (SNTP, RTC, etc.) |

### Optional: Calendar Dates

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `winter_start_month` | int | `10` | Winter lock start (October) |
| `winter_start_day` | int | `15` | Winter lock start day |
| `winter_end_month` | int | `4` | Winter lock end (April) |
| `winter_end_day` | int | `15` | Winter lock end day |
| `summer_start_month` | int | `6` | Summer lock start (June) |
| `summer_start_day` | int | `1` | Summer lock start day |
| `summer_end_month` | int | `8` | Summer lock end (August) |
| `summer_end_day` | int | `31` | Summer lock end day |

### Optional: Demand & Interval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `heat_demand_id` | string | `"any_pid_requesting_heat"` | Binary sensor for heat demand |
| `cool_demand_id` | string | `"any_pid_requesting_cool"` | Binary sensor for cool demand |
| `check_interval` | duration | `1min` | Evaluation frequency |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `select.${seasonal_mode_id}` | Select | Mode selector (HEAT/COOL/SANITARY_ONLY) |
| `text_sensor.${seasonal_mode_id}_reason` | Text | Why current mode was set (CALENDAR_LOCK/DEMAND) |
| `text_sensor.${seasonal_mode_id}_season` | Text | Current season classification |
| `binary_sensor.${seasonal_mode_id}_summer` | Binary (internal) | Compatibility: true when COOL |
| `binary_sensor.${heat_demand_id}` | Binary | Stub — extend with your demand logic |
| `binary_sensor.${cool_demand_id}` | Binary | Stub — extend with your demand logic |

## Usage Example

```yaml
packages:
  seasonal: !include
    file: packages/coordinators/seasonal_mode.yaml
    vars:
      seasonal_mode_id: "hp_mode"
      seasonal_mode_name: "Heat Pump Mode"
      time_id: "sntp_time"
```

### Demand Sensor Extension (Required)

The demand binary sensors are stubs — your device config **must** extend them with actual zone aggregation:

```yaml
binary_sensor:
  - id: !extend any_pid_requesting_heat
    lambda: |-
      return id(pid_radiant_zone1_is_heating).state ||
             id(pid_radiant_zone2_is_heating).state ||
             id(pid_fancoil_zone1_is_heating).state;

  - id: !extend any_pid_requesting_cool
    lambda: |-
      return id(pid_radiant_zone1_is_cooling).state ||
             id(pid_fancoil_zone1_is_cooling).state;
```

## Integration Tips

- **Calendar dates**: Defaults are tuned for Milan, Italy (Mediterranean climate). Adjust for your latitude.
- **Manual override**: The select entity is exposed to Home Assistant, so users can manually force a mode. Calendar gates will override manual selections at the next check interval.
- **Shoulder season behavior**: The system starts each shoulder season in SANITARY_ONLY and only transitions to HEAT or COOL when actual PID demand appears.
- **Zone subscription**: Radiant, heat-only radiant, and fancoil components all accept `seasonal_mode_id` as a required variable and automatically extend the select's `on_value` trigger.
