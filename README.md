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

| Component                       | Type        | Description                                                        | Docs                                                       |
| ------------------------------- | ----------- | ------------------------------------------------------------------ | ---------------------------------------------------------- |
| **Trend Sensor**                | Utility     | Rate-of-change calculator with sliding window averaging            | [docs/trend-sensor.md](docs/trend-sensor.md)               |
| **Failover Sensor**             | Utility     | 3-tier sensor failover with automatic recovery                     | [docs/failover-sensor.md](docs/failover-sensor.md)         |
| **Proportional Demand Sensor**  | Utility     | Converts sensor readings to 0-100% demand signals                  | [docs/proportional-demand.md](docs/proportional-demand.md) |
| **Fancoil Boost Coordinator**   | Coordinator | Base + Boost pattern for radiant floor + fancoil hybrid control    | [docs/fancoil-boost.md](docs/fancoil-boost.md)             |
| **MEV Ventilation Coordinator** | Coordinator | Multi-demand ventilation orchestration with humidity state machine | [docs/mev-ventilation.md](docs/mev-ventilation.md)         |

### Package Structure

```
packages/
├── utils/                          # Standalone utility components
│   ├── trend_sensor.yaml           # Rate-of-change with smoothing
│   ├── failover_sensor.yaml        # Multi-tier sensor failover
│   └── proportional_demand_sensor.yaml  # Sensor → demand % mapping
└── coordinators/                   # Multi-component orchestration
    ├── fancoil_boost.yaml          # Radiant + fancoil hybrid control
    └── mev_ventilation.yaml        # Multi-demand ventilation
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
    file: vesta/packages/utils/trend_sensor.yaml
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
    file: packages/utils/trend_sensor.yaml
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

- [Getting Started](docs/getting-started.md) - Installation and first steps
- [Principles](docs/principles.md) - Foundational design principles
- [Two-Zone Radiant + Fancoil](examples/two_zone_radiant_fancoil.yaml) - Boost coordination for hybrid zones
- [MEV Two-Demand Ventilation](examples/mev_two_demand.yaml) - Proportional ventilation driven by humidity + CO2
- [Contributing](CONTRIBUTING.md) - How to contribute components and improvements

---

## License

[MIT](LICENSE) - Use freely in personal and commercial projects.
