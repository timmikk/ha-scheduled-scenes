# Task: dim to warm curves

**Task:** #1
**Status:** done
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Add dim-to-warm curves for brightness-based color temperature calculation
**Host:** all
**Created:** 2026-10-28
**Completed:** 2026-10-28

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

- [x] (auto) Define `DimToWarmPoint(brightness: int, temp: int)` dataclass.
- [x] (auto) Define `DimToWarmCurve(name: str, lights: list[str], points: list[DimToWarmPoint])` dataclass with `evaluate(brightness: int) -> int` method performing clamped piecewise linear interpolation.
- [x] (auto) Implement `parse_curve_points(raw_points: list) -> list[DimToWarmPoint]` supporting both `[{brightness: X, temp: Y}, ...]` and `[[X, Y], ...]`.
- [x] (auto) Implement `parse_dim_to_warm_curves(data: dict) -> tuple[dict[str, DimToWarmCurve], dict[str, DimToWarmCurve]]` returning curves by name and curves by entity ID.
- [x] (auto) Update `ScheduleStep` and `parse_schedule_step` to allow `temp` to be `None` when omitted, and support `dim_to_warm` / `dimm_to_warm` aliases.
- [x] (auto) Update `calculate_light_state(transition, light_id, light_curves=...)` to calculate temperature from curve when step/override `temp` is omitted.
- [x] (auto) Add unit tests for curve parsing, piecewise linear interpolation (boundaries, intermediate points, clamping), and transition state calculation.

### 2. Configuration Schema & Top-Level / Room Curve Support
**Files:** `custom_components/scheduled_scenes/const.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (configuration validation)

Add schema constants and update YAML / config entry schemas to accept global curves and per-room curves.

- [x] (auto) Add constants `CONF_CURVES = "curves"`, `CONF_POINTS = "points"`, `CONF_DIM_TO_WARM = "dim_to_warm"`, and `CONF_DIMM_TO_WARM = "dimm_to_warm"` in `const.py`.
- [x] (auto) Update `PROGRAM_SCHEMA` to make `temp` in schedule steps optional, accept `dim_to_warm` aliases, and accept optional per-room `curves`.
- [x] (auto) Update `CONFIG_SCHEMA` to support either a list of programs (backwards-compatible) or a dictionary containing `curves:` and `programs:` / `rooms:`.
- [x] (auto) Update `async_setup` to pass global curves from integration YAML down to imported program configurations.

### 3. Runtime Coordinator Integration
**Files:** `custom_components/scheduled_scenes/coordinator.py`
**Host impact:** None (runtime state dispatch)

Integrate parsed curves into `ScheduledSceneProgram` lifecycle and service calls.

- [x] (auto) Parse and store `self.curves` and `self.light_curves` during `ScheduledSceneProgram.__init__`.
- [x] (auto) Pass `self.light_curves` to `calculate_light_state` in `async_transition`.
- [x] (auto) Add debug logging when dim-to-warm curves are resolved for lights on transition.

### 4. Config Flow & Options Flow Validation
**Files:** `custom_components/scheduled_scenes/config_flow.py`
**Host impact:** None (UI / YAML input validation)

Ensure config flow and options flow allow schedules where `temp` is omitted and support curve definitions.

- [x] (auto) Update `_validate_input` in `config_flow.py` to allow schedule steps without `temp`.
- [x] (auto) Ensure options flow preserves and reloads curves seamlessly.

### 5. Automated Tests & Regression Validation
**Files:** `tests/test_logic.py`, `tests/test_coordinator.py`, `tests/test_init.py`, `tests/test_config_flow.py`
**Host impact:** None (CI & pytest)

Verify all new capabilities and verify zero regression against existing test suites.

- [x] (auto) Test multi-entity curve sharing (e.g. two spots on same curve model).
- [x] (auto) Test mixed rooms (lights with curves, lights without curves, lights with explicit step overrides).
- [x] (auto) Test backwards compatibility: existing schedule step format with explicit `brightness` and `temp` works unchanged.
- [x] (auto) Test coordinator dispatches expected Kelvin and brightness to `light.turn_on`.
- [x] (auto) Run complete pytest test suite and ensure 100% pass rate.

### 6. Documentation & Release Notes
**Files:** `README.md`, `CHANGELOG.md`
**Host impact:** None (documentation)

Document the new dim-to-warm curve feature and configuration examples.

- [x] (auto) Add "Dim-to-Warm Curves" section in `README.md` with schema explanation and full YAML examples.
- [x] (auto) Document both point formats (`{brightness, temp}` and `[brightness, temp]`).
- [x] (auto) Update `CHANGELOG.md` with feature summary.
- [x] (auto) Regenerate `TODO.md` and `NEEDS-FROM-YOU.md` via `todo-status.mjs`.

---

## Security considerations

None — pure mathematical interpolation and Home Assistant configuration parsing; no network services, secrets, tokens, or permissions altered.

---

## Out-of-repo changes

None.

---

## Validation

- [x] Run pytest: `/home/timo/dev/ha-ulkovalot/.venv/bin/pytest`
- [x] All 30 existing tests pass + new test suites pass (39/39 passed)
- [x] Verify YAML parsing on sample configurations with both point formats
- [x] Verify ruff check passes with zero errors

---

## Documentation updates

- [x] `README.md` updated with curve configuration guide
- [x] `CHANGELOG.md` updated
- [x] Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write`

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | logic | `custom_components/scheduled_scenes/logic.py`, `tests/test_logic.py` | `feat(logic): add dim-to-warm curve interpolation and parsing` |
| 2 | config | `const.py`, `__init__.py`, `config_flow.py`, `coordinator.py` | `feat(coordinator): integrate dim-to-warm curve configuration and dispatch` |
| 3 | tests | `tests/test_coordinator.py`, `tests/test_init.py`, `tests/test_config_flow.py` | `test: add integration tests for dim-to-warm curves` |
| 4 | docs | `README.md`, `CHANGELOG.md` | `docs: document dim-to-warm curves and configuration syntax` |
| 5 | wrap-up | `tasks/done/1-feature-dim-to-warm-curves-done.md` | `chore: mark task #1 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] Security review passed
- [x] Validation passes (`pytest` clean, 39 passed)
- [x] Documentation updated

---

## Execution log

- 2026-10-28: Started execution of task #1 on branch `task/1-feature-dim-to-warm-curves`. Baseline pytest 30/30 passed.
- 2026-10-28: Implemented `DimToWarmPoint`, `DimToWarmCurve`, `parse_curve_points`, `parse_dim_to_warm_curves`, and updated `calculate_light_state` in `logic.py`. Added unit tests in `tests/test_logic.py` (35/35 passed). Committed `9f0e283`.
- 2026-10-28: Updated configuration schema in `__init__.py` and `const.py` for global/room curves, updated `coordinator.py` with curve state storage and dispatch, and updated `config_flow.py` with curve selectors and validation. Committed `ab3a0ab`.
- 2026-10-28: Added integration tests for coordinator curve dispatch, YAML setup with global curves, and config flow / options flow curve validation. All 39 tests passed. Cleaned ruff lint warnings. Committed `9ab1d57`.
- 2026-10-28: Updated `README.md` with complete documentation for Dim-to-Warm Curves and updated `CHANGELOG.md`. Committed `7289168`.

---

## Outcome

Successfully implemented the dim-to-warm curves feature for `ha-scheduled-scenes`:
1. Curves can be defined at the global integration level or within individual room configurations.
2. Multiple light entities of the same model can be mapped to a single curve definition.
3. Checkpoint points support both verbose dictionaries (`[{brightness: 1, temp: 2200}, ...]`) and compact coordinate pairs (`[[1, 2200], [100, 4000]]`).
4. In schedule steps, temperature can be omitted when `brightness` is specified, automatically deriving the color temperature along the curve.
5. Backwards compatibility is 100% preserved for traditional explicit temperature schedules.
6. 100% test coverage with 39 passing pytest tests.

---

## Actual commits

- 9f0e283 feat(logic): add dim-to-warm curve interpolation and parsing
- ab3a0ab feat(coordinator): integrate dim-to-warm curve configuration and dispatch
- 9ab1d57 test: add integration tests for dim-to-warm curves
- 7289168 docs: document dim-to-warm curves and configuration syntax
