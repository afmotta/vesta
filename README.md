# Vesta Climate Framework

**Production-proven ESPHome packages for multi-zone HVAC systems that run without the cloud, without Home Assistant, and without crossing your fingers.**

---

## The Problem

Building a multi-zone climate control system on ESPHome is surprisingly hard. The basic tutorials get you a thermostat. But a real building — multiple floors, radiant floors, fancoils, ventilation, seasonal switching — hits problems that no tutorial covers:

- **What happens when your temperature sensor dies mid-winter?** Your PID goes blind and your pipes could freeze.
- **What happens when Home Assistant restarts?** Every automation stops. Your house drifts.
- **How do you coordinate radiant floors and fancoils?** They fight each other without orchestration.
- **How do you handle shoulder seasons?** Manual switching between heat and cool is fragile and forgettable.
- **How do you scale from 1 zone to 13?** Copy-paste YAML breaks at scale.

These aren't hypothetical. They're problems we hit running a 13-zone, 3-floor residential HVAC system in Milan. Vesta is the framework we built to solve them.

---

## What Vesta Gives You

### Autonomy That Survives Failures

Every Vesta component runs on the ESP32. No cloud. No Home Assistant dependency. No network required for core operation.

- **Sensor failover**: If your primary sensor dies, Vesta switches to a backup automatically — and switches back when it recovers
- **Edge-first control**: PID loops, boost coordination, ventilation state machines all run locally
- **HA-enhanced, not HA-dependent**: Home Assistant adds dashboards and tuning knobs, but the house stays comfortable without it

### Composable Building Blocks

Vesta isn't a monolithic system. It's a library of packages you compose together:

- Start with a **single PID zone** for one room
- Add **sensor failover** for reliability
- Add a **fancoil boost coordinator** when radiant alone isn't enough
- Add **seasonal mode** to automate heat/cool switching
- Add **ventilation control** driven by CO₂ and humidity
- Scale to as many zones as your building needs

Each package declares its inputs as variables. Wire them together with ESPHome's standard `!include` and `vars`. No custom components, no C++ required — just YAML.

### Production-Proven Patterns

Every component in Vesta has run in production on real HVAC hardware controlling a real building. The patterns are proven through seasons of operation:

- **PID tuning** that works for both slow radiant floors and fast fancoils
- **Anti-oscillation** logic that prevents equipment short-cycling
- **Graceful degradation** at every level — from sensor failover to emergency shutdown
- **Demand-based control** that only runs equipment when actually needed

---

## Components

### Utility Components

| Component | What It Solves |
| --------- | -------------- |
| [**Failover Sensor**](docs/failover-sensor.md) | Automatic switchover between primary and backup sensors with recovery |
| [**Trend Sensor**](docs/trend-sensor.md) | Rate-of-change calculation for predictive control decisions |
| [**Proportional Demand Sensor**](docs/proportional-demand.md) | Converts raw readings (CO₂, humidity, IAQ) into 0-100% demand signals |

### Zone Control

| Component | What It Solves |
| --------- | -------------- |
| [**PID Controller**](docs/pid.md) | Production-wrapped PID with diagnostic sensors and safe defaults |
| [**PID Autotune**](docs/pid-autotune.md) | Automated gain discovery (basic + fancoil-safe variants) |
| [**Radiant**](docs/radiant.md) | Dual heat+cool radiant floor zone with slow PWM and override |
| [**Heat-Only Radiant**](docs/heat-only-radiant.md) | Simplified radiant zone for heating-only areas |
| [**Fancoil**](docs/fancoil.md) | Fancoil unit with PID control and 0-10V analog output |

### Pumps & Valves

| Component | What It Solves |
| --------- | -------------- |
| [**Direct Pump**](docs/direct-pump.md) | On/off pump driven by zone demand |
| [**Mixing Pump**](docs/mixing-pump.md) | Mixing valve + circulation pump with PID and supply temp sensor |

### Coordinators

| Component | What It Solves |
| --------- | -------------- |
| [**Fancoil Boost**](docs/fancoil-boost.md) | Orchestrates radiant + fancoil as complementary layers (Base + Boost) |
| [**Seasonal Mode**](docs/seasonal-mode.md) | Automates heat/cool switching with calendar gates + PID demand |
| [**MEV Ventilation**](docs/mev-ventilation.md) | Multi-demand ventilation with humidity cascade state machine |

### Device Drivers

| Component | What It Solves |
| --------- | -------------- |
| [**Modbus Relay Board**](docs/modbus-relay-board.md) | 8-relay Modbus expansion board (e.g., Kincony KC868) |
| [**Modbus Analog Board**](docs/modbus-analog-board.md) | 8-channel 0-10V Modbus analog output board |

---

## Quick Start

### Prerequisites

- **ESPHome** 2026.3.0 or later
- **ESP32** board (ESP-IDF or Arduino framework)
- **Home Assistant** (optional — for monitoring, dashboards, and tuning)

No custom components or external libraries required. Vesta uses only standard ESPHome YAML features.

### Add a Component

```yaml
# Local include
packages:
  room_failover: !include
    file: vesta/packages/components/failover_sensor.yaml
    vars:
      sensor_id: "living_room_temp"
      sensor_name: "Living Room Temperature"
      unit_of_measurement: "°C"
      device_class: "temperature"
      primary_sensor: ha_living_room_temp
      secondary_sensor: local_living_room_temp
```

```yaml
# Or from GitHub
packages:
  room_failover:
    url: github://your-username/vesta-climate-framework
    file: packages/components/failover_sensor.yaml
    vars:
      sensor_id: "living_room_temp"
      sensor_name: "Living Room Temperature"
      unit_of_measurement: "°C"
      device_class: "temperature"
      primary_sensor: ha_living_room_temp
      secondary_sensor: local_living_room_temp
```

Every component documents its required and optional variables in a header comment block. Components include their dependencies automatically.

---

## Architecture Principles

Vesta is built on principles refined through production operation:

1. **Autonomous Core** — If HA dies, the network drops, the cloud disappears, the house stays comfortable
2. **Logic Lives on the Edge** — Control decisions run on ESP32 devices, not in HA automations
3. **HA-Enhanced, Not HA-Dependent** — HA adds visibility and convenience, not reliability
4. **Minimal Zone Contract** — Each zone needs only a mode, a setpoint, a sensor, and an output
5. **Match Thermal Inertia to Disturbance Patterns** — Slow systems handle slow changes; fast systems handle fast changes
6. **Heterogeneous Subsystem Support** — Mix radiant, fancoil, ventilation, and other systems freely

See [docs/principles.md](docs/principles.md) for the complete set with examples.

---

## Documentation

- [**Getting Started**](docs/getting-started.md) — Installation, first component, and learning path
- [**Principles**](docs/principles.md) — The design philosophy behind every component
- [**Examples**](examples/) — Complete working configurations you can adapt
- [**Contributing**](CONTRIBUTING.md) — How to contribute components and improvements

---

## License

[MIT](LICENSE) — Use freely in personal and commercial projects.
