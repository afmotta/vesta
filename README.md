# Vesta Climate Framework

**Production-proven ESPHome packages for multi-zone HVAC orchestration.**

Vesta (Roman goddess of the hearth) is a collection of reusable ESPHome YAML packages. 

These components solve real problems that multi-zone HVAC integrators face: sensor failover, proportional demand control, and multi-subsystem coordination.

---

## The Base + Boost Innovation

Vesta's flagship pattern treats radiant floor and fancoil systems as **complementary layers** rather than either/or alternatives:

- **Base Layer** (Radiant Floor): Efficient, comfortable baseline heating/cooling via PID control
- **Boost Layer** (Fancoil): Responsive capacity supplement that activates automatically when needed

The Fancoil Boost Coordinator uses three activation triggers:

1. **Reactive (Temperature)** - Temperature delta exceeds threshold
2. **Reactive (Humidity)** - Humidity exceeds threshold with hysteresis dead band
3. **Predictive (PID Saturation)** - PID output saturated with no temperature improvement

Deactivation requires ALL conditions to clear (AND logic), with anti-oscillation protection via minimum time-in-state. This pattern is not documented elsewhere in the ESPHome ecosystem.

---

## Components

### Utility Components

| Component | Description | Docs |
|-----------|-------------|------|
| **Trend Sensor** | Rate-of-change calculator with sliding window averaging | [docs/trend-sensor.md](docs/trend-sensor.md) |
| **Failover Sensor** | 3-tier sensor failover with automatic recovery | [docs/failover-sensor.md](docs/failover-sensor.md) |
| **Proportional Demand Sensor** | Converts sensor readings to 0-100% demand signals | [docs/proportional-demand.md](docs/proportional-demand.md) |
| **Dew Point Sensor** | Magnus formula dew point from humidity + temperature | [docs/dew-point-sensor.md](docs/dew-point-sensor.md) |

### Zone Components (PID Control)

| Component | Description | Docs |
|-----------|-------------|------|
| **PID Controller** | Production-tested PID wrapper with diagnostic sensors | [docs/pid.md](docs/pid.md) |
| **PID Autotune** | Automated PID gain discovery (basic + fancoil-safe variants) | [docs/pid-autotune.md](docs/pid-autotune.md) |
| **Heat-Only Radiant** | Heat-only radiant zone with slow PWM and manual override | [docs/heat-only-radiant.md](docs/heat-only-radiant.md) |
| **Radiant** | Dual heat+cool radiant floor zone | [docs/radiant.md](docs/radiant.md) |
| **Fancoil** | Fancoil unit with PID control for 0-10V analog output | [docs/fancoil.md](docs/fancoil.md) |

### Pump Components

| Component | Description | Docs |
|-----------|-------------|------|
| **Direct Pump** | Simple on/off pump from binary trigger | [docs/direct-pump.md](docs/direct-pump.md) |
| **Mixing Pump** | Mixing valve + pump with PID and Dallas sensor | [docs/mixing-pump.md](docs/mixing-pump.md) |

### Coordinators

| Component | Description | Docs |
|-----------|-------------|------|
| **Seasonal Mode** | Three-tier calendar + demand seasonal mode coordinator | [docs/seasonal-mode.md](docs/seasonal-mode.md) |
| **Fancoil Boost** | Base + Boost pattern for radiant + fancoil hybrid control | [docs/fancoil-boost.md](docs/fancoil-boost.md) |
| **MEV Ventilation** | Multi-demand ventilation with humidity state machine | [docs/mev-ventilation.md](docs/mev-ventilation.md) |

### Device Drivers

| Component | Description | Docs |
|-----------|-------------|------|
| **Modbus Relay Board** | 8-relay Modbus expansion board driver | [docs/modbus-relay-board.md](docs/modbus-relay-board.md) |
| **Modbus Analog Board** | 8-channel 0-10V Modbus analog output driver | [docs/modbus-analog-board.md](docs/modbus-analog-board.md) |

### Package Structure

```
packages/
├── components/                          # Standalone reusable components
│   ├── trend_sensor.yaml                # Rate-of-change with smoothing
│   ├── failover_sensor.yaml             # Multi-tier sensor failover
│   ├── proportional_demand_sensor.yaml  # Sensor → demand % mapping
│   ├── dew_point_sensor.yaml            # Dew point calculation
│   ├── pid.yaml                         # PID controller wrapper
│   ├── pid_sensors.yaml                 # PID diagnostic sensors
│   ├── pid_autotune.yaml                # PID autotune button
│   ├── pid_autotune_with_fancoil.yaml   # Safe autotune variant
│   ├── heat_only_radiant.yaml           # Heat-only radiant zone
│   ├── radiant.yaml                     # Dual heat+cool radiant zone
│   ├── fancoil.yaml                     # Fancoil unit zone
│   ├── direct_pump.yaml                 # Simple pump control
│   └── mixing_pump.yaml                 # Mixing valve + pump with PID
├── coordinators/                        # Multi-component orchestration
│   ├── seasonal_mode.yaml               # Calendar + demand mode selection
│   ├── fancoil_boost.yaml               # Radiant + fancoil hybrid control
│   └── mev_ventilation.yaml             # Multi-demand ventilation
└── devices/                             # Hardware device drivers
    └── modbus-io/                       # Modbus I/O board drivers
        ├── modbus_relay_board.yaml      # 8-relay board aggregator
        ├── modbus_relay_switch.yaml     # Individual relay switch
        ├── modbus_analog_outputs_board.yaml  # 8-channel analog board
        └── modbus_analog_output.yaml    # Individual analog output
```

---

## Quick Start

### Prerequisites

- **ESPHome** 2025.12.0 or later
- **ESP32** board (ESP-IDF or Arduino framework)
- **Home Assistant** (optional but recommended for monitoring)

### Local Include

```yaml
packages:
  trend: !include
    file: vesta/packages/components/trend_sensor.yaml
    vars:
      sensor_id: "my_trend"
      source_sensor: sensor.room_temperature
      unit_of_measurement: "°C/min"
```

### GitHub Remote Include

```yaml
packages:
  trend:
    url: github://your-username/vesta-climate-framework
    file: packages/components/trend_sensor.yaml
    vars:
      sensor_id: "my_trend"
      source_sensor: sensor.room_temperature
      unit_of_measurement: "°C/min"
```

Each component documents its required and optional variables in a header comment block. See individual component docs for full parameter references.

---

## Architecture Philosophy

Vesta is built on principles refined through production operation:

1. **HA-Enhanced, Not HA-Dependent** - Components work autonomously; Home Assistant adds monitoring and overrides
2. **Logic Lives on the Edge** - Climate decisions run on ESP32 devices, not in the cloud or HA
3. **Minimal Zone Contract** - Each zone needs only a temperature sensor, a setpoint, and an output
4. **Match Thermal Inertia to Disturbance Patterns** - Slow systems (radiant) handle slow changes; fast systems (fancoil) handle fast changes
5. **Heterogeneous Subsystem Support** - Mix radiant floors, fancoils, ventilation, and other systems within one framework

See [docs/principles.md](docs/principles.md) for the complete set of foundational principles.

---

## Documentation

- [Getting Started](docs/getting-started.md) - Installation, first steps, and component reference
- [Principles](docs/principles.md) - Foundational design principles
- [PID Controller](docs/pid.md) - PID wrapper with diagnostic sensors
- [Seasonal Mode](docs/seasonal-mode.md) - Three-tier automatic mode selection
- [Two-Zone Radiant + Fancoil](examples/two_zone_radiant_fancoil.yaml) - Boost coordination for hybrid zones
- [MEV Two-Demand Ventilation](examples/mev_two_demand.yaml) - Proportional ventilation driven by humidity + CO2
- [Contributing](CONTRIBUTING.md) - How to contribute components and improvements

---

## License

[MIT](LICENSE) - Use freely in personal and commercial projects.
