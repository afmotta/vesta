# PID Autotune

Automated PID gain discovery with optional fancoil interference prevention.

## What It Does

The autotune packages create a button in Home Assistant that triggers ESPHome's built-in PID autotune algorithm. Press the button, and the system will oscillate the output to determine optimal Kp, Ki, and Kd gains for your specific hardware.

Two variants are provided:

- **Basic** (`pid_autotune.yaml`) — Simple autotune button for any PID controller
- **With Fancoil** (`pid_autotune_with_fancoil.yaml`) — Disables fancoil boost and PID before autotuning to prevent interference

## When to Use Which

| Variant | Use Case |
|---------|----------|
| Basic | Standalone PID zones (mixing valves, single-output zones) |
| With Fancoil | Zones with both radiant PID and fancoil PID (prevents boost from interfering) |

## Parameter Reference

### Basic Autotune

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pid_name` | string | Yes | - | Display name for the button |
| `pid_id` | string | Yes | - | ID of the PID climate to autotune |

### With Fancoil Variant

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `room_slug` | string | Yes | - | Room identifier for entity IDs |
| `room_name` | string | Yes | - | Display name for the button |
| `pid_id` | string | Yes | - | ID of the radiant PID to autotune |
| `fancoil_pid_id` | string | Yes | - | ID of the fancoil PID to disable during autotune |
| `boost_active_global` | string | Yes | - | ID of the boost active binary sensor to monitor |

## Usage Examples

### Basic

```yaml
packages:
  autotune: !include
    file: packages/components/pid_autotune.yaml
    vars:
      pid_name: "Radiant Living Room"
      pid_id: pid_radiant_living_room
```

### With Fancoil Protection

```yaml
packages:
  autotune: !include
    file: packages/components/pid_autotune_with_fancoil.yaml
    vars:
      room_slug: "living_room"
      room_name: "Living Room"
      pid_id: pid_radiant_living_room
      fancoil_pid_id: pid_fancoil_living_room
      boost_active_global: living_room_boost_active
```

## Integration Tips

- Run autotune when the zone is at a **stable temperature** and no other disturbances are present
- The with-fancoil variant automatically turns off the fancoil PID and waits for boost to deactivate before starting
- After autotune completes, note the suggested gains from the ESPHome logs and update your configuration permanently
