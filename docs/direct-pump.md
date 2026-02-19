# Direct Pump

Simple circulation pump control — turns a relay on/off based on a binary sensor trigger.

## What It Does

Wraps a binary sensor signal to control a pump relay. When the trigger sensor is ON, the pump turns on; when OFF, the pump turns off. No PID or mixing logic — just direct on/off control.

Use this for direct circulation pumps where the boiler/heat pump manages water temperature and the pump just needs to circulate.

## Parameter Reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sensor_id` | string | Yes | - | Binary sensor ID that triggers pump |
| `area_name` | string | Yes | - | Area name for log messages |
| `relay_id` | string | Yes | - | Switch ID for the pump relay |

### Exposed Entities

| Entity | Type | Description |
|--------|------|-------------|
| `binary_sensor.${sensor_id}_wrapped` | Binary (internal) | Pump trigger wrapper |

## Usage Example

```yaml
packages:
  pump: !include
    file: packages/components/direct_pump.yaml
    vars:
      sensor_id: first_floor_demand
      area_name: "First Floor"
      relay_id: relay_14
```

## Integration Tips

- **Trigger signal**: The `sensor_id` is typically a demand aggregation binary sensor (e.g., "any zone on this floor requesting heat").
- For **mixing valve + pump** setups where the pump also needs PID-driven valve position control, use `mixing_pump.yaml` instead.
