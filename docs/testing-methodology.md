# ESPHome Testing Methodology

A portable recipe for adding automated test coverage to a repository of
ESPHome YAML packages. It assumes no custom C++ components — just packages
included via `!include` + `vars`, with logic in template entities, lambdas,
scripts, and automations. Copy this doc (and a `tests/` skeleton) into any
repo that fits that shape.

## Prerequisites: design for testability

The methodology only works if packages follow three conventions. Enforce
them in code review:

1. **Dependency injection by convention.** Packages take every external
   entity (sensors, switches, climates, outputs) as a `var` — never a
   hardcoded global ID. Then any input can be replaced by a `template` stub.
2. **Parameterized timing.** Delays, anti-cycling minimums, and
   `update_interval`s are vars with production defaults. Tests compress
   hours of behavior into seconds by overriding them; no fake clock exists,
   so this is the only lever.
3. **Observable state.** Internal state machines publish their state as a
   (text) sensor entity. Tests assert on the published contract, never on
   internals.

## The three layers

| Layer | Command | Catches | Cost |
|-------|---------|---------|------|
| 1. Validate | `esphome config <harness>` | Schema errors, renamed vars, broken `!include` paths, ID collisions | Seconds |
| 2. Compile | `esphome compile <harness>` (host platform) | C++ errors inside lambdas — layer 1 never compiles them | ~20 s cold, no-op cached |
| 3. Behavior | host binary + `aioesphomeapi` + pytest | Logic bugs: wrong transitions, broken hysteresis/anti-cycling, math errors | ~Seconds per test |

All three layers share one artifact per package: a **harness config** in
`tests/harness/<package>.yaml`. The key enabler is ESPHome's `host`
platform: any config compiles to a native Linux binary running the full
runtime (template entities, scripts, automations, the API server) — no
device, no flashing. ESPHome core tests itself the same way.

The meaningful *unit* is the package: a harness exercising one package with
stubbed inputs is the unit test. The same machinery pointed at a config
composing several packages is the e2e test. Don't extract lambdas into
header files to unit-test them in C++ — it breaks the "just YAML" property
for marginal gain.

## Harness anatomy

```yaml
esphome:
  name: t-my-package        # binary lands in .esphome/build/<name>/.pioenvs/<name>/program

host:

logger:
  level: DEBUG

api:                        # no encryption needed locally
  actions:                  # input injection, callable from pytest
    - action: set_primary
      variables: { value: float }
      then:
        - sensor.template.publish:
            id: stub_primary
            state: !lambda "return value;"

sensor:
  - platform: template      # bare stub: stays NaN (= "failed sensor")
    id: stub_primary        # until a test publishes a value
    internal: true

packages:
  dut: !include             # the package under test, included exactly
    file: ../../packages/my_package.yaml   # as a user would include it
    vars:
      input_sensor: stub_primary
      update_interval: 100ms       # time compression via existing vars
```

- Stub every input: template sensor / binary sensor / switch. For entities
  the package *controls* (numbers, switches), use optimistic templates and
  assert on their state.
- If the package drives a real component interface (e.g. calls
  `climate.control`), instantiate the real component (e.g. a `pid` climate)
  over a no-op `template` output (`write_action: [lambda: ";"]`) — a stub
  would bypass the interface under test.
- `NaN` travels fine through API actions as a float — use it to simulate
  sensor failure.

## pytest driver

A shared fixture (copy `tests/e2e/conftest.py` from a repo already using
this methodology) does: `esphome compile` (cached) → launch the binary →
wait for the API port → connect with `aioesphomeapi` → subscribe to states.
Tests then read like scenarios:

```python
await h.call("set_primary", value=21.5)            # inject input
await h.wait_for("my_output", lambda s: s.state == "Primary")  # await contract
```

## Hard-won gotchas

- **API `object_id` derives from the entity *name*, not its `id`.**
  `name: "Test Temp Tier"` → `test_temp_tier`. Pick harness names to match
  the ids your tests assert on.
- **Template `binary_sensor`s are evaluated every loop iteration** (and
  reject `update_interval`); template `sensor`s poll, default 60 s. Any
  hardcoded `update_interval` in a package is a testability bug — make it
  an optional var with the current value as default.
- **Host preferences persist to a file in the working directory** (anything
  with `restore_value`/`restore_mode`). Launch each test binary in a fresh
  temp dir or state leaks between runs.
- **uart / modbus / gpio don't run on the host platform.** Hardware-bound
  packages stay at layers 1–2, with an ESP32 cross-compile in a nightly
  workflow instead of per-PR.
- **`aioesphomeapi` can impersonate Home Assistant**
  (`send_home_assistant_state`) — use it to prove `platform: homeassistant`
  config sensors fall back to hardcoded defaults when HA never shows up.
- **Run `esphome config` on your `examples/` too** (with a stub
  `secrets.yaml` generated in CI). Examples rot silently: duplicate
  top-level keys and wrong relative `!include` paths are invisible until a
  user tries them.

## Project layout & CI

Keep the test suite a self-contained uv project under `tests/`, so the repo
root stays YAML-first and contributors need one command:

```
tests/
  pyproject.toml   # pinned esphome + aioesphomeapi + pytest (+ uv.lock)
  harness/         # one ESPHome config per package — used by all 3 layers
  e2e/             # conftest.py + test_<package>.py
```

```
uv run --project tests pytest tests/e2e/
```

CI (GitHub Actions): a fast job running layer 1 on every harness and
example, then a job running pytest (which compiles host binaries as a side
effect), with `~/.platformio` and `tests/harness/.esphome` cached. Pin
ESPHome in `pyproject.toml`; bumping the pin and re-locking *is* the
compatibility test for raising `min_version`.

## Rollout order for a new repo

1. Harness + layer 1 in CI for every package — instant regression net.
2. Layer 3 for the simplest pure-logic package — proves the plumbing.
3. Layer 3 for the state machines / coordinators — the tests that earn
   trust: activation triggers, hysteresis bands, anti-cycling timers,
   safety overrides.
4. ESP32 nightly compile for examples and hardware-bound packages.
5. One composition e2e config mirroring a real deployment.
