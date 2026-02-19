# Modbus Relay Board

8-relay Modbus expansion board driver with individual relay control and connectivity monitoring.

## What It Does

Manages a complete 8-relay Modbus board. Creates the `modbus_controller`, instantiates 8 individual relay switches mapped to sequential coil registers, and monitors board connectivity with a status sensor.

Use this for Modbus relay expansion boards like the KC868-A16 or similar 8-relay RS485 modules.

## How It Works

```
ESPHome ──RS485──→ Modbus Relay Board (address 0x02)
                   ├── Coil 0x0000 → Relay 1
                   ├── Coil 0x0001 → Relay 2
                   ├── ...
                   └── Coil 0x0007 → Relay 8
```

The board driver creates one `modbus_controller` and includes `modbus_relay_switch.yaml` eight times with sequential register addresses. Each relay is exposed as an ESPHome switch.

## Parameter Reference

### Board Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `controller_id` | string | Yes | - | Unique ID for this modbus_controller |
| `controller_name` | string | Yes | - | Display name for status sensor |
| `modbus_address` | hex/int | Yes | - | Modbus slave address (e.g., `0x02`) |
| `modbus_bus_id` | string | Yes | - | ID of the modbus bus |
| `update_interval` | duration | No | `5s` | Polling interval |
| `id_offset` | int | No | `0` | Offset for relay numbering across boards |

### Individual Switch Parameters (modbus_relay_switch.yaml)

These are passed automatically by the board driver:

| Parameter | Type | Description |
|-----------|------|-------------|
| `controller_id` | string | Modbus controller reference |
| `switch_number` | int | Relay number (1-8) |
| `register_address` | hex | Coil register (0x0000-0x0007) |
| `id_offset` | int | Numbering offset from parent |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `switch.relay_{1+offset}` through `switch.relay_{8+offset}` | Switch | Individual relay controls |
| `binary_sensor.${controller_id}_status` | Binary (internal) | Board connectivity |

## Usage Example

### Single Board

```yaml
packages:
  relays: !include
    file: packages/devices/modbus-io/modbus_relay_board.yaml
    vars:
      controller_id: relay_board_1
      controller_name: "Relay Board 1"
      modbus_address: 0x02
      modbus_bus_id: rs485_bus
```

### Multiple Boards (Staggered IDs)

```yaml
packages:
  relays_ground: !include
    file: packages/devices/modbus-io/modbus_relay_board.yaml
    vars:
      controller_id: relay_board_ground
      controller_name: "Ground Floor Relays"
      modbus_address: 0x02
      modbus_bus_id: rs485_bus
      id_offset: 0      # Relays 1-8

  relays_first: !include
    file: packages/devices/modbus-io/modbus_relay_board.yaml
    vars:
      controller_id: relay_board_first
      controller_name: "First Floor Relays"
      modbus_address: 0x03
      modbus_bus_id: rs485_bus
      id_offset: 8      # Relays 9-16
```

## Integration Tips

- **id_offset**: When using multiple boards, stagger the offset by 8 per board (0, 8, 16, ...) so relay IDs don't collide.
- **Modbus bus**: The `modbus_bus_id` must reference a `modbus:` component defined in your device config with the correct UART settings (typically 9600 baud, 8N1).
- **Update interval**: 5s is conservative. For faster relay response, reduce to 2s. For less bus traffic, increase to 10s.
- **Board compatibility**: Works with any 8-relay Modbus board that uses sequential coil registers starting at 0x0000.
