# Task: brightness control

**Task:** #2
**Status:** pending
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Add room brightness stepping, estimation, and brightness distribution curves
**Host:** all
**Created:** 2026-10-28
**Completed:** —

## Context

Currently, `ha-scheduled-scenes` operates entirely on time-based schedules: light brightness and color temperature are calculated continuously from the active schedule interval. However, users frequently need interactive physical control (e.g., via wireless push-buttons, Zigbee remotes, wall switches, or dashboard controls) to increase or decrease room brightness in discrete steps (e.g. +10% / -10%).

Supporting interactive brightness adjustment introduces four core requirements:
1. **Room Brightness Distribution Curves ("Room Brightness Curve"):**
   In multi-light rooms, different fixtures serve different lighting functions (e.g., subtle accent lights, task downlights, floor lamps). A flat 50% brightness across all lights is rarely visually pleasing. At 50% room brightness, accent/mood lights may already look best at 100% while main ceiling spots should only be at 30%. This feature introduces room brightness distribution curves mapping overall room brightness (0–100%) to individual light brightness percentages via piecewise linear interpolation.
2. **Dim-to-Warm Utilization:**
   When room brightness changes (or when an individual light's brightness is calculated via the room curve), each fixture's color temperature must be evaluated using its configured dim-to-warm curve. As the user dims or brightens the room, lights smoothly warm up or cool down according to their physical dim-to-warm profile.
3. **Smooth Initial Start Brightness Estimation:**
   When an increase or decrease button is pressed for the first time while lights are on, the integration must avoid abrupt jumps or moving in the wrong direction. If the lights are currently at an arbitrary brightness level (from the schedule or an earlier setting), the system inspects the current physical brightness of active lights in the room, inverts the room curves to estimate the current overall room brightness percentage, and applies the step relative to that estimated baseline.
4. **Manual Override & Automatic Brightness Disabling:**
   Applying a manual brightness adjustment suspends automatic scheduled transitions so that periodic timer updates do not immediately override the user's manual preference. The manual override persists until all lights in the room turn off, the schedule switch is toggled, a resume service is called, or an optional auto-resume timeout expires.

## Affected hosts

- `all` — Component-scoped logic, services, and configuration within `custom_components/scheduled_scenes/`.

---

## Work items

### 1. Mathematical Model: Brightness Distribution Curves & Curve Inversion
**Files:** `custom_components/scheduled_scenes/logic.py`, `tests/test_logic.py`
**Host impact:** None (pure mathematical logic)

Implement brightness curve data structures, piecewise linear interpolation, curve inversion, room brightness estimation, and combined brightness + dim-to-warm light state calculation.

- [ ] (auto) Define `BrightnessPoint(room_brightness: int, light_brightness: int)` dataclass.
- [ ] (auto) Define `BrightnessCurve(name: str, lights: list[str], points: list[BrightnessPoint])` dataclass with `evaluate(room_brightness: int) -> int` (clamped piecewise linear interpolation) and `invert(light_brightness: int) -> int` (resolving room brightness percentage for a given light brightness).
- [ ] (auto) Implement `parse_brightness_points(raw_points: Any) -> list[BrightnessPoint]` supporting both dicts (`[{room_brightness: X, light_brightness: Y}, ...]`) and coordinate pairs (`[[X, Y], ...]`).
- [ ] (auto) Implement `parse_brightness_curves(data: Any) -> tuple[dict[str, BrightnessCurve], dict[str, BrightnessCurve]]` returning curves by name and curves by entity ID.
- [ ] (auto) Implement `estimate_room_brightness(current_light_brightnesses: dict[str, int], brightness_curves: dict[str, BrightnessCurve] | None) -> int` estimating overall room brightness from active physical light states.
- [ ] (auto) Implement `calculate_manual_light_state(room_brightness: int, light_id: str, brightness_curves: dict[str, BrightnessCurve] | None, dim_to_warm_curves: dict[str, DimToWarmCurve] | None, default_temp: int = 2700) -> tuple[int, int]` computing target `(brightness_pct, color_temp_kelvin)` for a light at a given room brightness.
- [ ] (auto) Add unit tests for curve evaluation, inversion, estimation, and combined brightness + dim-to-warm state resolution.

### 2. Runtime Coordinator & Service Execution
**Files:** `custom_components/scheduled_scenes/coordinator.py`, `custom_components/scheduled_scenes/const.py`
**Host impact:** None (runtime state dispatch)

Integrate manual brightness tracking, step-based adjustments, schedule suppression, and physical state estimation into `ScheduledSceneProgram`.

- [ ] (auto) Add `self.manual_brightness: int | None = None` and `self.brightness_curves: dict[str, BrightnessCurve]` to `ScheduledSceneProgram`.
- [ ] (auto) Update `_async_periodic_callback` to bypass scheduled light transitions while `self.manual_brightness is not None`.
- [ ] (auto) Implement `async_adjust_brightness(step: int | None = None, brightness: int | None = None, transition: float | None = None) -> None`:
  - If `step` is provided and `self.manual_brightness is None`, estimate current room brightness from physical light states via `estimate_room_brightness`.
  - Calculate clamped target room brightness in `[0, 100]`.
  - Dispatch calculated brightness and dim-to-warm color temperature to all program lights via `light.turn_on` (or `light.turn_off` if light target brightness is 0).
  - Record `self.manual_brightness = target`.
- [ ] (auto) Implement `async_resume_schedule(transition: float | None = None)` clearing manual brightness and immediately executing `async_transition`.
- [ ] (auto) Update `_async_light_state_change`: when all lights turn off (`not self.is_any_light_on()`), clear `self.manual_brightness = None` so next turn-on follows regular schedule.
- [ ] (auto) Support optional `manual_override_timeout` in program config to automatically resume schedule after N minutes.

### 3. Service Registration & Configuration Schema
**Files:** `custom_components/scheduled_scenes/const.py`, `custom_components/scheduled_scenes/__init__.py`, `custom_components/scheduled_scenes/services.yaml`
**Host impact:** None (configuration & HA service bus)

Expose brightness adjustment and resume services to Home Assistant automations, dashboards, and blueprints.

- [ ] (auto) Add constants `CONF_BRIGHTNESS_CURVES = "brightness_curves"`, `SERVICE_ADJUST_BRIGHTNESS = "adjust_brightness"`, `SERVICE_RESUME_SCHEDULE = "resume_schedule"`, `ATTR_STEP = "step"`.
- [ ] (auto) Update `PROGRAM_SCHEMA` and `CONFIG_SCHEMA` to validate `brightness_curves` globally and per-program.
- [ ] (auto) Register domain services `scheduled_scenes.adjust_brightness` and `scheduled_scenes.resume_schedule`.
- [ ] (auto) Register per-program legacy service aliases: `<program>_adjust_brightness`, `<program>_resume_schedule`.
- [ ] (auto) Define UI schemas and documentation in `services.yaml`.

### 4. Diagnostics & Entity State Reporting
**Files:** `custom_components/scheduled_scenes/sensor.py`, `custom_components/scheduled_scenes/switch.py`
**Host impact:** None (HA entity state)

Reflect manual override status and current room brightness in sensor attributes.

- [ ] (auto) Update `ScheduledSceneSensor.extra_state_attributes` to expose `manual_override: bool`, `manual_brightness: int | None`, and `estimated_brightness: int | None`.
- [ ] (auto) Ensure toggling `ScheduledSceneSwitch` on resets manual override and resumes schedule.

### 5. Automated Tests & Regression Validation
**Files:** `tests/test_logic.py`, `tests/test_coordinator.py`, `tests/test_init.py`
**Host impact:** None (CI & pytest)

Verify all new features and verify zero regression against existing test suites.

- [ ] (auto) Test step increase/decrease from schedule baseline without sudden jumps.
- [ ] (auto) Test multi-light room brightness distribution curve: accent lights at 100% while main lights at 30% on 50% room brightness.
- [ ] (auto) Test dim-to-warm temperature evaluation under manual brightness changes.
- [ ] (auto) Test that periodic scheduled transitions do not overwrite manual brightness.
- [ ] (auto) Test resumption of schedule on `resume_schedule` call and on all lights turning off.
- [ ] (auto) Run complete pytest test suite and ensure 100% pass rate.
- [ ] (auto) Verify `ruff check .` passes with zero errors.

### 6. Documentation & Release Notes
**Files:** `README.md`, `CHANGELOG.md`
**Host impact:** None (documentation)

Document room brightness curves, stepping services, and button automation recipes.

- [ ] (auto) Add "Room Brightness Curves & Stepping" section in `README.md` with schema documentation and YAML examples.
- [ ] (auto) Document `scheduled_scenes.adjust_brightness` and `scheduled_scenes.resume_schedule` services.
- [ ] (auto) Provide automation example for connecting physical Zigbee buttons / remotes.
- [ ] (auto) Update `CHANGELOG.md` with feature summary.
- [ ] (auto) Run `make todo` (`todo-status.mjs --write`) to refresh TODO board.

---

## Security considerations

None — pure component-level logic and HA service registration; no network listeners, external credentials, or elevated permissions.

---

## Out-of-repo changes

None.

---

## Validation

- [ ] Run pytest: `/home/timo/dev/ha-ulkovalot/.venv/bin/pytest`
- [ ] All 39 existing tests pass + new test suites pass (45+ total)
- [ ] Verify ruff linting: `/home/timo/.local/bin/ruff check .`
- [ ] Verify `node ~/dev/dev-tools/scripts/todo-status.mjs --check` passes cleanly

---

## Documentation updates

- [ ] `README.md` updated with brightness curve schema and button adjustment examples
- [ ] `CHANGELOG.md` updated
- [ ] Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write`

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | logic | `logic.py`, `tests/test_logic.py` | `feat(logic): add room brightness curves, estimation, and inversion` |
| 2 | coordinator | `coordinator.py`, `const.py`, `tests/test_coordinator.py` | `feat(coordinator): support manual brightness stepping and schedule override` |
| 3 | config | `__init__.py`, `services.yaml`, `sensor.py`, `tests/test_init.py` | `feat(config): register adjust_brightness and resume_schedule services` |
| 4 | docs | `README.md`, `CHANGELOG.md` | `docs: document room brightness curves and button adjustment` |
| 5 | wrap-up | `tasks/done/2-feature-brightness-control-done.md` | `chore: mark task #2 as done` |

---

## Definition of done

- [ ] All work items checked off
- [ ] Security review passed
- [ ] Validation passes (`pytest` and `ruff` clean)
- [ ] Documentation updated
