# Task: dim to warm curves

**Task:** #1
**Status:** pending
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Add dim-to-warm curves for brightness-based color temperature calculation
**Host:** all
**Created:** 2026-10-28
**Completed:** —

## Context

Currently, `ha-scheduled-scenes` requires each schedule checkpoint to define both `brightness` (0–100%) and color temperature `temp` (Kelvin), or to override both per light. For rooms with dim-to-warm lights, users have to manually calculate and specify matching Kelvin values at every time checkpoint. Furthermore, different light models have different physical dim-to-warm characteristics (e.g. Philips Hue 2200K–4000K vs. Ikea Trådfri 2000K–4000K vs. warm-glow recessed spots), making manual coordination cumbersome across multiple lights and rooms.

This feature introduces first-class **dim-to-warm curve** support:
1. Curves can be defined once in configuration with a name, a list of target entity IDs (allowing multiple entities to share the same curve model), and a list of brightness-to-temperature checkpoints.
2. Checkpoint points support both explicit dict format (`[{brightness: 1, temp: 2200}, {brightness: 100, temp: 4000}]`) and compact coordinate pairs (`[[1, 2200], [100, 4000]]`).
3. In room schedule configurations, schedule steps can specify `brightness` without `temp` (or alias `dim_to_warm` / `dimm_to_warm`). When `temp` is omitted, any light assigned to a curve automatically derives its color temperature from the curve at that brightness.
4. Traditional schedules with explicit `temp` continue to work unchanged; an explicit `temp` always takes precedence over curve derivation.
5. Transitions smoothly interpolate: if both boundary steps use curves, intermediate states follow the exact physical curve; if one boundary step has an explicit temperature override, linear color temperature interpolation is maintained.

## Affected hosts

- `all` — Component-scoped logic and configuration within `custom_components/scheduled_scenes/`.

---

## Work items

### 1. Mathematical Model & Piecewise Linear Curve Interpolation
**Files:** `custom_components/scheduled_scenes/logic.py`, `tests/test_logic.py`
**Host impact:** None (pure mathematical logic)

Implement curve point structures, piecewise linear interpolation, curve parsing, and curve-aware light state calculation.

- [ ] (auto) Define `DimToWarmPoint(brightness: int, temp: int)` dataclass.
- [ ] (auto) Define `DimToWarmCurve(name: str, lights: list[str], points: list[DimToWarmPoint])` dataclass with `evaluate(brightness: int) -> int` method performing clamped piecewise linear interpolation.
- [ ] (auto) Implement `parse_curve_points(raw_points: list) -> list[DimToWarmPoint]` supporting both `[{brightness: X, temp: Y}, ...]` and `[[X, Y], ...]`.
- [ ] (auto) Implement `parse_dim_to_warm_curves(data: dict) -> tuple[dict[str, DimToWarmCurve], dict[str, DimToWarmCurve]]` returning curves by name and curves by entity ID.
- [ ] (auto) Update `ScheduleStep` and `parse_schedule_step` to allow `temp` to be `None` when omitted, and support `dim_to_warm` / `dimm_to_warm` aliases.
- [ ] (auto) Update `calculate_light_state(transition, light_id, light_curves=...)` to calculate temperature from curve when step/override `temp` is omitted.
- [ ] (auto) Add unit tests for curve parsing, piecewise linear interpolation (boundaries, intermediate points, clamping), and transition state calculation.

### 2. Configuration Schema & Top-Level / Room Curve Support
**Files:** `custom_components/scheduled_scenes/const.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (configuration validation)

Add schema constants and update YAML / config entry schemas to accept global curves and per-room curves.

- [ ] (auto) Add constants `CONF_CURVES = "curves"`, `CONF_POINTS = "points"`, `CONF_DIM_TO_WARM = "dim_to_warm"`, and `CONF_DIMM_TO_WARM = "dimm_to_warm"` in `const.py`.
- [ ] (auto) Update `PROGRAM_SCHEMA` to make `temp` in schedule steps optional, accept `dim_to_warm` aliases, and accept optional per-room `curves`.
- [ ] (auto) Update `CONFIG_SCHEMA` to support either a list of programs (backwards-compatible) or a dictionary containing `curves:` and `programs:` / `rooms:`.
- [ ] (auto) Update `async_setup` to pass global curves from integration YAML down to imported program configurations.

### 3. Runtime Coordinator Integration
**Files:** `custom_components/scheduled_scenes/coordinator.py`
**Host impact:** None (runtime state dispatch)

Integrate parsed curves into `ScheduledSceneProgram` lifecycle and service calls.

- [ ] (auto) Parse and store `self.curves` and `self.light_curves` during `ScheduledSceneProgram.__init__`.
- [ ] (auto) Pass `self.light_curves` to `calculate_light_state` in `async_transition`.
- [ ] (auto) Add debug logging when dim-to-warm curves are resolved for lights on transition.

### 4. Config Flow & Options Flow Validation
**Files:** `custom_components/scheduled_scenes/config_flow.py`
**Host impact:** None (UI / YAML input validation)

Ensure config flow and options flow allow schedules where `temp` is omitted and support curve definitions.

- [ ] (auto) Update `_validate_input` in `config_flow.py` to allow schedule steps without `temp`.
- [ ] (auto) Ensure options flow preserves and reloads curves seamlessly.

### 5. Automated Tests & Regression Validation
**Files:** `tests/test_logic.py`, `tests/test_coordinator.py`, `tests/test_init.py`, `tests/test_config_flow.py`
**Host impact:** None (CI & pytest)

Verify all new capabilities and verify zero regression against existing test suites.

- [ ] (auto) Test multi-entity curve sharing (e.g. two spots on same curve model).
- [ ] (auto) Test mixed rooms (lights with curves, lights without curves, lights with explicit step overrides).
- [ ] (auto) Test backwards compatibility: existing schedule step format with explicit `brightness` and `temp` works unchanged.
- [ ] (auto) Test coordinator dispatches expected Kelvin and brightness to `light.turn_on`.
- [ ] (auto) Run complete pytest test suite and ensure 100% pass rate.

### 6. Documentation & Release Notes
**Files:** `README.md`, `CHANGELOG.md`
**Host impact:** None (documentation)

Document the new dim-to-warm curve feature and configuration examples.

- [ ] (auto) Add "Dim-to-Warm Curves" section in `README.md` with schema explanation and full YAML examples.
- [ ] (auto) Document both point formats (`{brightness, temp}` and `[brightness, temp]`).
- [ ] (auto) Update `CHANGELOG.md` with feature summary.
- [ ] (auto) Regenerate `TODO.md` and `NEEDS-FROM-YOU.md` via `todo-status.mjs`.

---

## Security considerations

None — pure mathematical interpolation and Home Assistant configuration parsing; no network services, secrets, tokens, or permissions altered.

---

## Out-of-repo changes

None.

---

## Validation

- [ ] Run pytest: `/home/timo/dev/ha-ulkovalot/.venv/bin/pytest`
- [ ] All 30 existing tests pass + new test suites pass
- [ ] Verify YAML parsing on sample configurations with both point formats

---

## Documentation updates

- [ ] `README.md` updated with curve configuration guide
- [ ] `CHANGELOG.md` updated
- [ ] Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write`

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | logic | `custom_components/scheduled_scenes/logic.py`, `tests/test_logic.py` | `feat(logic): add dim-to-warm curve interpolation and parsing` |
| 2 | config | `const.py`, `__init__.py`, `config_flow.py`, `coordinator.py` | `feat(coordinator): integrate dim-to-warm curve configuration and dispatch` |
| 3 | tests | `tests/test_coordinator.py`, `tests/test_init.py`, `tests/test_config_flow.py` | `test: add integration tests for dim-to-warm curves` |
| 4 | docs | `README.md`, `CHANGELOG.md` | `docs: document dim-to-warm curves and configuration syntax` |
| 5 | wrap-up | `tasks/done/1-feature-dim-to-warm-curves.md` | `chore: mark task #1 as done` |

---

## Definition of done

- [ ] All work items checked off
- [ ] Security review passed
- [ ] Validation passes (`pytest` clean)
- [ ] Documentation updated
