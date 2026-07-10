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
- **Board compatibility**: Works with any 8-relay Modbus board that uses sequential coil registers starting at 0x0000 (e.g. KC868-A16). For 32-relay boards, see the 32-Channel variant below.

## 32-Channel Variant

`modbus_relay_board_32ch.yaml` is a drop-in sibling of the 8-relay board above, sized for the
**Waveshare Modbus RTU Relay 32CH** board (ADR-0014's standardized relay bank for both HVAC and
lighting). Same parameter interface, same defaults, 32 channels instead of 8 — **with one
difference: no connectivity status sensor** (see below).

### Board Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `controller_id` | string | Yes | - | Unique ID for this modbus_controller |
| `controller_name` | string | No | - | Accepted for interface parity with the 8-ch board's `!include` shape; currently unused, since there's no status sensor to name (see "No Connectivity Sensor" below) — safe to omit |
| `modbus_address` | hex/int | Yes | - | Modbus slave address (e.g., `0x02`) |
| `modbus_bus_id` | string | Yes | - | ID of the modbus bus |
| `update_interval` | duration | No | `5s` | Polling interval. Unchanged from the 8-ch board's default; not re-validated for 32 coils' worth of polling traffic per cycle — see Integration Tips |
| `id_offset` | int | No | `0` | Offset for relay numbering across boards; supports negative values (see below); no lower-bound guard, no type check |

### Exposed Entities

These are alternate configurations of the same package (pick one `id_offset` per instance),
not entities produced simultaneously:

| Entity | Type | Description |
|--------|------|-------------|
| `switch.relay_{1+offset}` through `switch.relay_{32+offset}` (positive `id_offset`, e.g. `0`) | Switch | Individual relay controls |
| `switch.relay_0` through `switch.relay_31` (with `id_offset: -1`, 0-based scheme) | Switch | Individual relay controls |

No `binary_sensor.*_status` entity — see "No Connectivity Sensor" below.

### No Connectivity Sensor

Unlike the 8-ch board, this variant does **not** expose a connectivity `binary_sensor`. The
8-ch board's status sensor works because it polls an independent holding/input register
(`register_type: read`) that doesn't overlap any relay's coil. The 32CH board has no such
register — every documented coil address (`0x0000`–`0x001F`) is one of the 32 relay channels
themselves, and the "all-relay control" address (`0x00FF`) isn't independent of relay state
either. Polling any of them under a `device_class: connectivity` label would just alias that
relay's own on/off state (e.g. address `0x0000` == `relay_1`'s coil) — a user switching relay 1
off would make the board falsely report as disconnected. Rather than ship a misleading sensor,
this package omits it. Communication failures are still visible: ESPHome's `modbus_controller`
marks each switch unavailable on read timeout, so per-relay failure detection is unaffected.

### Differences from the 8-Channel Board

- **File**: `modbus_relay_board_32ch.yaml` (32 `!include modbus_relay_switch.yaml` entries,
  coils `0x0000`–`0x001F`).
- **No connectivity sensor** — see above.
- **Stagger by 32, not 8.** The 8-ch board's Integration Tips above say "stagger `id_offset`
  by 8 per board" — that guidance is for 8-ch boards only. Mixing an 8-ch and a 32-ch board (or
  two 32-ch boards) on the same device requires staggering by however many IDs the *previous*
  board actually consumes (32 for this board), or relay ids collide silently.
- **Negative `id_offset` is supported.** Verified with a real `esphome config` run: passing
  `id_offset: -1` as a numeric `vars` value (not a substitution string) correctly yields
  `switch_number` values starting at `0` (`relay_0`..`relay_31`). This lets a 0-based consumer
  (e.g. lighting's `relay_0..relay_31` binding scheme) use the same package without a shift step
  — as long as `id_offset` is passed as an integer, not a quoted string (ESPHome's substitution
  arithmetic rejects `int + string`). There is no lower-bound guard: `id_offset` below `-1`
  produces an invalid entity id (e.g. `relay_-1`) — this is the caller's responsibility to avoid.
  Only `id_offset: 0` is exercised by the committed, compile-checked
  `vesta/examples/modbus_relay_board_32ch.yaml`; the negative-offset finding above was verified
  with an uncommitted scratch config (see the originating spec's Design Notes) and has no
  persisted regression check in this repo.

### Usage Example

```yaml
packages:
  relays: !include
    file: packages/devices/modbus-io/modbus_relay_board_32ch.yaml
    vars:
      controller_id: relay_board_1
      controller_name: "Relay Board 1"
      modbus_address: 0x02
      modbus_bus_id: rs485_bus
      id_offset: 0
```
