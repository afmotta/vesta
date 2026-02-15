# Foundational Principles

These nine principles emerged from building and operating a production multi-zone climate control system. They represent hard-won insights about what works when ESP32 devices control real HVAC equipment in a real building.

---

## 1. Integrated Climate Orchestration

Heating, cooling, and ventilation are one system, not three silos.

A room's temperature, humidity, and air quality are interdependent. Running the dehumidifier affects temperature. Opening a radiant zone affects the mixing valve. Ventilation fan speed affects humidity load. Treating these as separate automations leads to fighting between systems.

Vesta components are designed to be composed together. The fancoil boost coordinator considers both temperature and humidity. The MEV ventilation controller cascades through fan-only, dehumidifying, and cooling states based on combined conditions.

## 2. Single Source of Truth for Mode

All zones synchronize to one heat/cool mode.

When a building has a single heat pump or generator, every zone must agree on whether the system is heating or cooling. There's no "heat the bedroom while cooling the kitchen" when both share the same supply water temperature.

This is modeled as a single binary sensor (`summer_mode` or `cooling_mode_sensor`) that every coordinator reads. Mode changes propagate instantly to all zones.

## 3. HA-Enhanced, Not HA-Dependent

The system operates autonomously. Home Assistant adds visibility and convenience, not reliability.

Home Assistant is excellent for dashboards, notifications, and manual overrides. But if HA goes down for maintenance, a firmware update, or a crash, the house must stay comfortable.

All control decisions happen on ESP32 devices. HA provides optional tuning parameters (thresholds, delays) and fallback sensor data, but the core logic never depends on HA being available. Vesta components use `platform: homeassistant` sensors for configuration values with hardcoded fallback defaults.

## 4. Minimal Zone Contract

Each zone needs exactly: a mode, a setpoint, a temperature sensor, and an output.

Zones should be easy to add without restructuring the system. A new room needs a temperature sensor, a relay or valve, and inclusion in the zone configuration. Everything else (PID tuning, boost coordination, failover) layers on top of this minimal contract.

Optional additions like humidity, CO2, and air quality sensors enable more sophisticated control (fancoil boost, ventilation demand) but aren't required for basic operation.

## 5. Autonomous Core

If Home Assistant dies, if the network drops, if the cloud disappears, the house stays comfortable.

This goes beyond principle #3. The autonomous core means that each ESP32 board can independently maintain temperature control with zero external dependencies. Modbus communication between boards provides sensor data and mode synchronization without any network infrastructure.

The failover sensor embodies this: Primary (HA) -> Secondary (direct ESP-to-ESP) -> Emergency (safe shutdown). Each tier is a graceful degradation, not a failure.

## 6. Logic Lives on the Edge

Climate control decisions run on ESP32 devices, not in HA automations or cloud services.

HA automations have latency, can miss events during restarts, and add a network round-trip to every decision. ESP32 devices evaluate conditions locally at 60-second intervals with zero network dependency.

The fancoil boost coordinator runs entirely on the ESP32. It reads local sensors, evaluates triggers, and controls local outputs. HA only sees the diagnostic entities it publishes.

## 7. Direct Board Communication

Boards talk to each other via Modbus RTU or ESPHome packet transfer. No HA in the middle.

When the master board needs sensor data from a slave, it reads Modbus registers directly over RS485. When a room sensor board broadcasts CO2 readings, it uses UDP packet transfer to the climate controller. Neither path involves Home Assistant.

This eliminates HA as a single point of failure for inter-board communication and reduces latency from seconds (HA round-trip) to milliseconds (direct serial/UDP).

## 8. Heterogeneous Subsystem Support

Different areas have different thermal needs requiring different technologies.

A bathroom needs fast response (fancoil) because of shower humidity spikes. A bedroom needs quiet, efficient background cooling (radiant floor). A kitchen with a garden door needs both: radiant for the base load, fancoil for when the door opens.

Vesta doesn't force a single subsystem type. The fancoil boost coordinator enables hybrid zones. The MEV ventilation controller handles mechanical ventilation. Each zone uses whatever hardware combination makes physical sense.

## 9. Match Thermal Inertia to Disturbance Patterns

Choose subsystems based on how the space is actually used.

Radiant floor heating/cooling has high thermal inertia: slow to start, slow to stop, but very efficient and comfortable once stable. Fancoils have low thermal inertia: fast response, but noisier and less efficient.

The key insight is matching the response speed to the disturbance pattern:

| Space Characteristic | Dominant Disturbance | Best Subsystem |
|---------------------|---------------------|----------------|
| Interior room, stable occupancy | Gradual temperature drift | Radiant (slow, efficient) |
| Room with exterior door | Sudden heat/cold gains | Fancoil (fast response) |
| Bathroom | Humidity spikes from showers | Fancoil (dehumidification) |
| Mixed-use room | Both gradual and sudden | Radiant + Fancoil (Base + Boost) |

The Base + Boost pattern from the fancoil boost coordinator is a direct application of this principle: radiant handles the slow, efficient base load while fancoils provide fast response to rapid changes.
