# Modbus Analog Outputs Board

8-channel 0-10V Modbus analog output board driver with PID-compatible outputs and diagnostics.

## What It Does

Manages a complete 8-channel 0-10V Modbus analog output board. Creates the `modbus_controller`, instantiates 8 individual analog outputs, and monitors board connectivity. Each output provides a PID-compatible float interface (0.0–1.0) that maps to 0-10V via Modbus register writes.

Use this for Modbus 0-10V DAC adapters that control fancoil fan speeds, variable pumps, or any other 0-10V actuator.

## How It Works

```
PID (0.0-1.0) → Template Output → Modbus Register (0-10000) → 0-10V Signal
                                                                    ↓
                                                              Fancoil Motor
```

Each channel creates:
1. A `number` entity (internal) for direct register control (0-10000 = 0-10V)
2. A `template output` that accepts PID float values (0.0-1.0) and scales to register range
3. Two diagnostic sensors: capacity percentage (0-100%) and voltage (0-10V)

## Parameter Reference

### Board Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `controller_id` | string | Yes | - | Unique ID for this modbus_controller |
| `controller_name` | string | Yes | - | Display name for status sensor |
| `modbus_address` | hex/int | Yes | - | Modbus slave address (e.g., `0x01`) |
| `modbus_bus_id` | string | Yes | - | ID of the modbus bus |
| `update_interval` | duration | No | `1s` | Polling interval (faster than relays) |
| `id_offset` | int | No | `0` | Offset for output numbering |

### Individual Output Parameters (modbus_analog_output.yaml)

Passed automatically by the board driver, but can also be used standalone:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `controller_id` | string | Yes | - | Modbus controller reference |
| `output_number` | int | Yes | - | Channel number (1-8) |
| `register_address` | hex | Yes | - | Holding register address |
| `output_id` | string | No | Auto-generated | Override for the output entity ID |
| `id_offset` | int | No | `0` | Numbering offset |
| `update_interval` | duration | No | `5s` | Diagnostic sensor update interval |

### Exposed Entities (per channel)

| Entity | Type | Description |
|--------|------|-------------|
| `output.analog_output_{N}` | Output | PID-compatible float output (0.0-1.0) |
| `sensor.analog_output_{N}_capacity` | Sensor | Current output as percentage |
| `sensor.analog_output_{N}_voltage` | Sensor | Current output as voltage (V) |
| `binary_sensor.${controller_id}_status` | Binary (internal) | Board connectivity |

## Usage Example

### Basic Setup

```yaml
packages:
  analog: !include
    file: packages/devices/modbus-io/modbus_analog_outputs_board.yaml
    vars:
      controller_id: analog_board_1
      controller_name: "Analog Board 1"
      modbus_address: 0x01
      modbus_bus_id: rs485_bus
```

### Connecting to Fancoil PID

```yaml
packages:
  analog: !include
    file: packages/devices/modbus-io/modbus_analog_outputs_board.yaml
    vars:
      controller_id: analog_board_1
      controller_name: "Analog Board 1"
      modbus_address: 0x01
      modbus_bus_id: rs485_bus

  fancoil: !include
    file: packages/components/fancoil.yaml
    vars:
      room_slug: "living_room"
      room_name: "Living Room"
      temperature_sensor: sensor.living_room_temp
      output_id: analog_output_1       # ← references board's output
      seasonal_mode_id: hp_mode
```

## Integration Tips

- **Faster polling**: Default 1s update interval is faster than relay boards because analog outputs need responsive control for smooth fan speed transitions.
- **Custom output IDs**: Pass `output_id` to individual analog outputs when you need meaningful names (e.g., `fancoil_living_room_output`) instead of `analog_output_1`.
- **Value range**: The Modbus register accepts 0-10000, representing 0.000V to 10.000V. The template output handles the scaling automatically.
