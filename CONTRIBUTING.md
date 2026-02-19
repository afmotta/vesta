# Contributing to Vesta Climate Framework

Thank you for your interest in contributing! Vesta welcomes components, improvements, examples, and documentation from the ESPHome community.

---

## Proposing New Components

Before writing code, open an issue describing:

1. **What the component does** - One paragraph explaining the problem it solves
2. **Why it belongs in Vesta** - How it fits the multi-zone climate control scope
3. **Parameter contract** - Required and optional variables with types and defaults
4. **Dependencies** - Which existing Vesta components it uses (if any)
5. **Source** - Whether it's extracted from a production system or newly created

Components should be:
- **Reusable** across different HVAC installations
- **Parameterized** with no hardcoded references to specific homes, rooms, or hardware
- **Self-contained** or dependent only on other Vesta packages

---

## YAML Coding Standards

### Formatting

- **Indentation:** 2 spaces (no tabs)
- **Key spacing:** Space after colon (`key: value`)
- **List items:** Dash with space (`- item`)
- **Line length:** Keep lines under 120 characters where practical
- **Comments:** Use `#` with a space after (`# Comment text`)

### Header Comment Block

Every component YAML file must start with a header comment block:

```yaml
# =============================================================================
# Component: trend_sensor.yaml
# Purpose:   Calculate rate of change per minute with sliding window smoothing
#
# Required vars:
#   sensor_id            - ID for the created trend sensor
#   source_sensor        - Sensor ID to analyze (e.g., sensor.room_temp)
#   unit_of_measurement  - Output unit (e.g., "°C/min", "%/min")
#
# Optional vars:
#   sensor_name          - Friendly name (default: "Trend Sensor")
#   window_size          - Smoothing window samples (default: 10)
#   accuracy_decimals    - Decimal precision (default: 2)
#   icon                 - MDI icon (default: "mdi:trending-up")
#   internal             - Hide from HA (default: false)
#
# Example:
#   packages:
#     trend: !include
#       file: packages/components/trend_sensor.yaml
#       vars:
#         sensor_id: "living_room_trend"
#         source_sensor: sensor.living_room_temperature
#         unit_of_measurement: "°C/min"
# =============================================================================
```

### Parameterization Pattern

All home-specific values must be substitution variables. Zero hardcoded references.

```yaml
# CORRECT - Fully parameterized
sensor:
  - platform: template
    id: ${sensor_id}
    name: ${sensor_name}

# WRONG - Hardcoded reference
sensor:
  - platform: template
    id: living_room_trend
    name: "Living Room Trend"
```

**Variable naming conventions:**
- Use `snake_case` for all variable names
- Suffix IDs with `_id` (e.g., `sensor_id`, `source_sensor_id`)
- Suffix names with `_name` (e.g., `sensor_name`, `room_name`)
- Suffix slugs with `_slug` (e.g., `zone_slug`, `component_slug`)
- Use `defaults:` block for optional variables with sensible defaults

```yaml
defaults:
  sensor_name: "Trend Sensor"
  window_size: "10"
  accuracy_decimals: "2"
  icon: "mdi:trending-up"
  internal: "false"
```

---

## Testing Expectations

### Required Validation

Before submitting a PR, verify:

1. **Config validation** - Component compiles without errors:
   ```bash
   esphome config your_test_device.yaml
   ```

2. **Standalone compilation** - Component works with only its declared parameters (no undeclared dependencies)

3. **Example compilation** - If you add or modify an example, it must pass `esphome config`

### Recommended Testing

- Test with at least one real ESP32 device if possible
- Verify Home Assistant entity exposure works correctly
- Test parameter defaults (omit optional vars, confirm behavior)

---

## Pull Request Guidelines

### PR Description

Include in your PR description:

1. **What** - Brief description of the change
2. **Why** - Problem it solves or improvement it provides
3. **Testing** - How you validated the change (config output, device test, etc.)
4. **Documentation** - Confirm docs are updated (component doc page, README table if new component)

### PR Checklist

- [ ] YAML follows coding standards (2-space indent, header comment, parameterized)
- [ ] No hardcoded home-specific references
- [ ] `esphome config` passes with a test device configuration
- [ ] Documentation updated (component doc page in `docs/`)
- [ ] README component table updated (if adding new component)
- [ ] Example updated or added (if applicable)

### Component Documentation

Every component needs a documentation page in `docs/` covering:

- **What it does** and when to use it
- **Parameter reference** table (name, type, required/optional, default, description)
- **Dependencies** on other Vesta packages
- **Usage example** showing `!include` with vars
- **How it works** - explanation of the logic for users who want to understand or customize

---

## Directory Structure

```
packages/
├── components/      # Standalone reusable components (no cross-dependencies)
├── coordinators/    # Multi-component orchestration (may depend on components)
└── devices/         # Hardware device drivers (e.g., modbus-io/)

docs/                # One .md file per component + getting-started, principles
examples/            # Complete, compilable example configurations
```

- **Components** are independent building blocks
- **Coordinators** orchestrate multiple systems and may depend on components
- **Devices** are hardware-specific drivers
- Place new packages in the appropriate category

---

## Questions?

Open an issue for discussion. We're happy to help shape component proposals before you invest time in implementation.
