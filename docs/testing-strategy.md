# Testing Strategy

This document proposes how to test Vesta. The short version: **Vesta's packages are far more testable than typical ESPHome YAML**, because every package already follows three conventions that testing needs:

1. **Dependency injection by convention.** Every package takes its inputs (sensors, switches, climates) as `vars`. Nothing reaches for a hardcoded global. That means any input can be replaced by a `template` stub in a test config.
2. **Parameterized timing.** Delays and intervals (`update_interval`, `min_time_in_state_seconds`, threshold sensors) are vars or runtime sensors, so tests can compress hours of HVAC behavior into seconds.
3. **Observable state.** Components publish their internal state as entities (`*_sensor_tier`, `*_boost_automation_state`, diagnostic sensors), so assertions don't need access to internals.

The missing piece is not a redesign — it's a harness. The proposal below adds one in three layers, ordered by cost. Each layer catches a different class of bug, and each is independently useful.

---

## The Three Layers

| Layer | Tool | Catches | Speed | Runs on |
|-------|------|---------|-------|---------|
| 1. Config validation | `esphome config` | Schema errors, broken `vars`/`defaults`, bad `!include` paths, ID collisions | Seconds | Every PR |
| 2. Compile checks | `esphome compile` (host + ESP32) | C++ errors in lambdas, type mismatches, missing IDs at link time | Minutes (cached) | Every PR (host), nightly (ESP32) |
| 3. Behavioral (e2e) | `host` platform binary + `aioesphomeapi` + pytest | Logic bugs: wrong failover tier, state machine misfires, broken anti-cycling, math errors | ~Seconds per test after compile | Every PR |

A key enabler for layers 2 and 3 is ESPHome's **`host` platform**: any config can be compiled into a native Linux binary that runs the full ESPHome runtime — template sensors, scripts, automations, the API server — with no ESP32 and no flashing. This is the same mechanism ESPHome core uses for its own integration test suite, so it is supported, idiomatic, and maintained upstream.

### Layer 1 — Config validation

For every package, a minimal **harness config** in `tests/harness/` includes the package with representative vars and stubs for its inputs. CI runs `esphome config tests/harness/*.yaml` plus the configs in `examples/`.

This alone catches the most common regression in a package-based repo: renaming a var, changing a default, or moving a file, and silently breaking every downstream consumer. Today nothing catches that until a user's build fails.

It is not a hypothetical layer: running it while preparing this proposal immediately caught two real bugs in `examples/` — both example configs had duplicate top-level `sensor:` keys (invalid YAML, rejected by ESPHome's loader) and used `packages/...` include paths that resolve relative to the including file, i.e. to a nonexistent `examples/packages/`. Neither example could have ever been loaded as shipped. Both are fixed in this branch.

### Layer 2 — Compile checks

`esphome config` does **not** compile the C++ inside lambdas — and the lambdas are where Vesta's real logic lives (failover tiers, trend math, boost conditions). `esphome compile` does.

- **Host compile** (fast lane, every PR): compile each harness config for the `host` platform. Uses the system gcc, no cross-toolchain download, and build dirs cache well in CI. This catches lambda typos, `isnan` vs `std::isnan`, bad `id()` references, etc.
- **ESP32 compile** (slow lane, nightly + release): compile `examples/*.yaml` and the `packages/devices/modbus-io/` harnesses for `esp32`. This is the only layer that exercises hardware-bound config (uart, modbus, gpio, ledc), and it verifies the `min_version` claim in the README against a real toolchain. Run it nightly and on tags rather than per-PR — with PlatformIO caching it's ~5–10 min, but it adds little per-PR signal beyond the host compile.

### Layer 3 — Behavioral tests (unit + e2e)

This is the layer that earns trust. The pattern:

1. **Harness config** (`tests/harness/<package>.yaml`, shared with layers 1–2):
   - targets the `host` platform with `api:` enabled (no encryption needed locally);
   - includes the package under test via `!include` exactly as a user would;
   - replaces every sensor input with a bare `template` sensor (publishes nothing until told — starts as `NaN`, which conveniently is also the "failed sensor" state);
   - exposes **API actions** (`api: actions:`) like `set_primary(value)` that call `sensor.template.publish`, so the test can inject any input — including `NaN` — over the native API;
   - compresses time via the package's existing vars (`update_interval: 250ms`, `min_time_in_state_seconds: 1`).

2. **pytest driver** (`tests/e2e/test_<package>.py`):
   - a fixture compiles the harness (cached), launches the binary as a subprocess, and connects with [`aioesphomeapi`](https://github.com/esphome/aioesphomeapi) — the same client Home Assistant uses;
   - tests call the injection actions, then await entity states and assert on them.

**"Unit" vs "e2e" in this codebase:** the meaningful unit in Vesta is the package, not a C++ function. A harness that exercises one package with stubbed inputs *is* the unit test. The same machinery pointed at a composition config (e.g. failover → PID → boost coordinator wired together, mirroring `examples/two_zone_radiant_fancoil.yaml` minus wifi/hardware) is the e2e test. Both live in the same pytest suite; only the harness config differs.

#### What the first test cases look like

**`failover_sensor`** (pure logic, the ideal first target):
- primary publishes 21.5 → output is 21.5, tier is `Primary`
- primary publishes `NaN`, secondary publishes 20.0 → output 20.0, tier `Secondary`
- both `NaN` → output `NaN`, tier `Emergency`
- primary recovers → tier returns to `Primary` (the recovery path the README promises)

**`trend_sensor`**: inject a ramp (0.1 °C every 250 ms), assert the trend converges near the expected °C/min within tolerance.

**`fancoil_boost`** (the state machine — highest-value target):
- cooling mode on, temp delta pushed above threshold → automation state becomes `Activating (reactive)`; after the (compressed) anti-cycling delay, select flips to `Fancoil Boost`, the radiant override switch turns on, the fancoil climate goes to `COOL`
- delta drops back below threshold *before* the delay elapses → timer cancels, state returns to `Idle`, select never flips (**this is the anti-short-cycling guarantee, now actually proven**)
- humidity trigger, predictive trigger, and the AND-logic deactivation each get their own case
- cooling mode off → no trigger fires regardless of temp

**`proportional_demand_sensor` / `pid`**: inject inputs, assert the 0–100 % mapping and that the PID output moves in the right direction and saturates where expected.

**HA-dependence tests**: `aioesphomeapi` can impersonate Home Assistant (`send_home_assistant_state`), so the "HA-enhanced, not HA-dependent" principle is testable too — assert that threshold sensors fall back to hardcoded defaults when no HA state ever arrives.

#### What stays out of scope for layer 3

- **`packages/devices/modbus-io/`**: uart/modbus don't run on the host platform. These stay at layers 1–2 (validate + ESP32 compile). If they ever grow logic worth testing, the modbus traffic itself would need a pty-based stub — possible, not worth it today.
- **Wall-clock-faithful timing**: there is no fake clock; tests compress time through vars instead. A 10-minute anti-cycle delay is tested as a 1-second delay — the *logic* (timer started, cancelled, completed) is what's under test, not the duration.

---

## Repository layout

The test suite is a self-contained [uv](https://docs.astral.sh/uv/) project under `tests/`, keeping the repository root YAML-first. `uv run --project tests pytest tests/e2e/` is the only command a contributor needs — uv provisions the virtualenv with the locked esphome/aioesphomeapi/pytest versions on first run.

```
tests/
  pyproject.toml            # uv project: pinned esphome, aioesphomeapi, pytest
  uv.lock                   # reproducible resolution, drives CI caching
  harness/                  # one ESPHome config per package (layers 1, 2, 3)
    failover_sensor.yaml
    trend_sensor.yaml
    fancoil_boost.yaml
    ...
  e2e/
    conftest.py             # compile-and-run fixture, aioesphomeapi helpers
    test_failover_sensor.py
    test_fancoil_boost.py
    ...
.github/workflows/
  ci.yml                    # lint → validate → host compile + e2e
  esp32.yml                 # nightly/tag: esp32 compile of examples + device drivers
```

Proofs of concept for both the simplest package (`failover_sensor`) and the most complex one (`fancoil_boost`) are included in this branch under `tests/` and verified end to end — each harness validates, compiles for the host platform in ~15–25 s cold (no-op when cached), and the behavioral suite passes:

```
$ pytest tests/e2e/ -v
tests/e2e/test_failover_sensor.py::test_failover_tier_cascade_and_recovery PASSED
tests/e2e/test_fancoil_boost.py::test_reactive_temp_activation_locks_radiant_and_enables_fancoil PASSED
tests/e2e/test_fancoil_boost.py::test_anti_cycling_timer_cancels_when_condition_clears PASSED
tests/e2e/test_fancoil_boost.py::test_reactive_humidity_activation PASSED
tests/e2e/test_fancoil_boost.py::test_predictive_activation_on_sustained_saturation PASSED
tests/e2e/test_fancoil_boost.py::test_deactivation_requires_temp_and_humidity PASSED
tests/e2e/test_fancoil_boost.py::test_season_change_ends_boost_immediately PASSED
============================== 7 passed in 43.63s ==============================
```

The `fancoil_boost` suite proves the harness pattern scales to the coordinators: it runs real `pid` climates over no-op template outputs, drives season/temperature/humidity/saturation through API actions, and asserts the full state-machine contract — including the anti-short-cycling guarantee (the activation timer cancels when the trigger clears early) and the immediate season-change safety override. The only package change it needed was making the hardcoded 30 s diagnostic `update_interval` an optional var (`diagnostics_update_interval`); the condition binary sensors needed nothing, since template binary sensors are evaluated every loop iteration.

## CI pipeline (GitHub Actions)

```yaml
# ci.yml (every push / PR)
jobs:
  validate:            # layer 1, ~1 min
    - astral-sh/setup-uv (cache keyed on tests/uv.lock)
    - uv sync --project tests --locked
    - uv run --project tests esphome config tests/harness/*.yaml examples/*.yaml
  behavioral:          # layers 2+3, ~3-5 min warm
    needs: validate
    - cache: ~/.platformio, tests/harness/.esphome
    - uv run --project tests pytest tests/e2e/   # compiles host binaries as a side effect

# esp32.yml (nightly + tags) — layer 2 slow lane
  esp32-compile:
    - cache: ~/.platformio
    - uv run --project tests esphome compile examples/*.yaml tests/harness/esp32/*.yaml
```

The ESPHome version is pinned in `tests/pyproject.toml` and locked in `tests/uv.lock`; bump it deliberately and re-lock — a CI run against a new ESPHome release is then a *compatibility test*, which is exactly the signal a packages repo needs before bumping `min_version`.

## Small testability refactors (worth doing, all backwards-compatible)

1. **Make hardcoded intervals optional vars.** A few diagnostic sensors hardcode `update_interval: 30s` (e.g. `temp_delta` in `fancoil_boost`). Moving these into `defaults:` keeps current behavior and lets tests compress time fully.
2. **Keep state observable.** New components should follow the existing convention of publishing a diagnostic text sensor for internal state — it's what makes black-box assertions possible.
3. **Don't extract lambdas into C++ headers for unit testing.** It's technically possible (`esphome: includes:` + Catch2), but it would break Vesta's "copy one YAML file, no custom components" property for marginal gain. Reserve it for any future lambda that outgrows a screenful; the behavioral layer covers today's lambdas through their observable contract.

## Suggested rollout order

1. **Layer 1 + CI skeleton** — immediate regression protection for every package, trivial to land.
2. **Layer 3 for `failover_sensor` + `trend_sensor`** — proves the harness pattern on pure-logic packages (PoC in this branch).
3. **Layer 3 for `fancoil_boost`, `seasonal_mode`, `mev_ventilation`** — the coordinators are where the risk lives; the state-machine tests are the highest-value tests in the repo.
4. **Layer 2 ESP32 nightly** — compatibility safety net for examples and device drivers.
5. **Composition e2e** — a two-zone host config mirroring the example, asserting the layers cooperate (boost flips → radiant override locks → PID resumes on release).
