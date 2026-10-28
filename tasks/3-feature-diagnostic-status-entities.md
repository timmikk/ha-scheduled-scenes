# Task: diagnostic status entities

**Task:** #3
**Status:** pending
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Add diagnostic status entities for room mode, curves in use, last command, brightness, and error state
**Host:** all
**Created:** 2026-10-28

## Context

`ha-scheduled-scenes` manages complex room lighting schedules, dim-to-warm Kelvin mappings, manual stepping overrides, and room brightness distribution curves. When testing, commissioning, or debugging room behavior in Home Assistant (e.g., verifying whether a physical button press overrode a schedule, why a light didn't transition, whether dim-to-warm is actively running, or why a room went off), users currently only have a single `Schedule Phase` sensor and a schedule switch.

To significantly improve visibility, debugging, and dashboard automation support, this feature introduces a complete suite of status and diagnostic entities for each configured program:
1. **Current Mode (`sensor.<program>_mode`):**
   Reports the operational mode of the room: `"off"` (disabled manually), `"auto-off"` (lights off/standby), `"auto"` (schedule actively controlling lights), or `"manual"` (manual brightness override active).
2. **Current Room Brightness (`sensor.<program>_current_brightness`):**
   Reports current overall room brightness (0–100%), whether evaluated from the active manual override, inverted from physical light states via room brightness distribution curves, or derived from the scheduled transition baseline.
3. **Last Command (`sensor.<program>_last_command`):**
   Tracks the most recent command or trigger dispatched to the room (e.g. `"set brightness"`, `"auto on"`, `"auto off"`, `"resume schedule"`, `"periodic update"`, `"enable"`, `"disable"`) with execution timestamp and parameters in state attributes.
4. **Dim-to-Warm In Use (`binary_sensor.<program>_dim_to_warm_in_use`):**
   Diagnostic binary sensor indicating whether dim-to-warm curves are active, including attributes with configured curves, assigned light entities, and currently active fixtures.
5. **Brightness Curve In Use (`binary_sensor.<program>_brightness_curve_in_use`):**
   Diagnostic binary sensor indicating whether room brightness distribution curves are active, listing mapped fixtures and curve configurations.
6. **Error / Problem State (`binary_sensor.<program>_problem`):**
   Standard Home Assistant `BinarySensorDeviceClass.PROBLEM` diagnostic entity flagging missing or unavailable light entities, invalid schedules, or failed service calls, exposing unavailable entity IDs and error logs in attributes.
7. **Device Grouping (`DeviceInfo`):**
   Attaches all entities (switch, phase sensor, diagnostic sensors, and binary sensors) to a unified Home Assistant Device per room, ensuring clean UI organization under Settings -> Devices & Services.

## Affected hosts

- `all` — Custom integration logic, sensor platforms, binary sensor platforms, and automated tests within `custom_components/scheduled_scenes/` and `tests/`.

---

## Work items

### 1. Coordinator State Tracking & Diagnostic Helpers
**Files:** `custom_components/scheduled_scenes/coordinator.py`
**Host impact:** None (component runtime state)

Extend `ScheduledSceneProgram` to track execution history, errors, operational mode, and light availability.

- [ ] (auto) Track `last_command: str`, `last_command_timestamp: datetime | None`, and `last_command_details: dict[str, Any]` in `ScheduledSceneProgram`.
- [ ] (auto) Implement `_record_command(command: str, details: dict[str, Any] | None = None) -> None` and invoke it on `async_turn_on`, `async_turn_off`, `async_adjust_brightness`, `async_resume_schedule`, `set_enabled`, and `_async_periodic_callback`.
- [ ] (auto) Track `_auto_disabled_by_lights_off: bool` to differentiate manual `"off"` from automatic `"auto-off"`.
- [ ] (auto) Implement `mode` property returning `"off"`, `"auto-off"`, `"auto"`, or `"manual"`.
- [ ] (auto) Implement `get_current_room_brightness() -> int` resolving brightness from manual override, room brightness curves, or schedule transitions.
- [ ] (auto) Track `last_error: str | None` and `last_error_timestamp: datetime | None`, catching and logging service call exceptions.
- [ ] (auto) Implement `get_unavailable_lights() -> list[str]` detecting missing or unavailable light entities in `self.hass.states`.
- [ ] (auto) Expose helper properties `is_dim_to_warm_in_use` and `is_brightness_curve_in_use`.

### 2. Diagnostic Sensor Platform Expansion
**Files:** `custom_components/scheduled_scenes/sensor.py`
**Host impact:** None (HA sensor platform)

Implement new sensor entities and attach all sensor entities to the program's `DeviceInfo`.

- [ ] (auto) Add `device_info` to `ScheduledSceneSensor` (`Schedule Phase`) targeting `(DOMAIN, entry_id)`.
- [ ] (auto) Implement `ScheduledSceneModeSensor(SensorEntity)` exposing `sensor.<program>_mode` with states `"off"`, `"auto-off"`, `"auto"`, and `"manual"`.
- [ ] (auto) Implement `ScheduledSceneBrightnessSensor(SensorEntity)` exposing `sensor.<program>_current_brightness` with unit `%` and detailed light state attributes.
- [ ] (auto) Implement `ScheduledSceneLastCommandSensor(SensorEntity)` exposing `sensor.<program>_last_command` with category `EntityCategory.DIAGNOSTIC` and timestamp attributes.
- [ ] (auto) Update `async_setup_entry` in `sensor.py` to instantiate and register all 4 sensor entities per program.

### 3. Binary Sensor Platform Implementation
**Files:** `custom_components/scheduled_scenes/binary_sensor.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (HA binary sensor platform)

Add `Platform.BINARY_SENSOR` support to `PLATFORMS` and create diagnostic binary sensor entities.

- [ ] (auto) Add `Platform.BINARY_SENSOR` to `PLATFORMS` in `custom_components/scheduled_scenes/__init__.py`.
- [ ] (auto) Create `custom_components/scheduled_scenes/binary_sensor.py` with `async_setup_entry`.
- [ ] (auto) Implement `ScheduledSceneDimToWarmBinarySensor(BinarySensorEntity)` with `EntityCategory.DIAGNOSTIC`.
- [ ] (auto) Implement `ScheduledSceneBrightnessCurveBinarySensor(BinarySensorEntity)` with `EntityCategory.DIAGNOSTIC`.
- [ ] (auto) Implement `ScheduledSceneProblemBinarySensor(BinarySensorEntity)` with `BinarySensorDeviceClass.PROBLEM` and `EntityCategory.DIAGNOSTIC`.

### 4. Switch Entity Device Linking
**Files:** `custom_components/scheduled_scenes/switch.py`
**Host impact:** None (HA switch platform)

Link existing `ScheduledSceneSwitch` entity to the program `DeviceInfo`.

- [ ] (auto) Add `device_info` property to `ScheduledSceneSwitch` linking to `(DOMAIN, entry_id)`.

### 5. Automated Tests & Regression Validation
**Files:** `tests/test_coordinator.py`, `tests/test_init.py`
**Host impact:** None (CI & pytest)

Verify all new status entities, state transitions, diagnostic attributes, and error reporting.

- [ ] (auto) Verify mode sensor transitions across off -> auto -> manual -> auto-off -> auto.
- [ ] (auto) Verify current brightness sensor with and without brightness curves and manual override.
- [ ] (auto) Verify last command sensor updates on service execution and light state changes.
- [ ] (auto) Verify dim-to-warm and brightness curve binary sensors with configured vs unconfigured programs.
- [ ] (auto) Verify problem binary sensor activates when a light entity becomes unavailable or missing.
- [ ] (auto) Verify backward compatibility: existing phase sensor and switch tests continue to pass 100%.
- [ ] (auto) Run `ruff check .` and pytest suite to guarantee clean code quality.

### 6. Documentation & Release Notes
**Files:** `README.md`, `CHANGELOG.md`
**Host impact:** None (documentation)

Document new status entities and debugging capabilities in integration documentation.

- [ ] (auto) Document available status and diagnostic entities in `README.md`.
- [ ] (auto) Update `CHANGELOG.md`.
- [ ] (auto) Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write` to update TODO board.

---

## Security considerations

None — pure Home Assistant entity and coordinator state exposure; no external network traffic, secrets, or elevated system privileges.

---

## Out-of-repo changes

None.

---

## Validation

- [ ] Run pytest: `/home/timo/dev/ha-ulkovalot/.venv/bin/pytest`
- [ ] All existing 44 tests pass + new test suites pass cleanly
- [ ] Verify ruff linting: `/home/timo/.local/bin/ruff check .`
- [ ] Verify `node ~/dev/dev-tools/scripts/todo-status.mjs --check` passes cleanly

---

## Documentation updates

- [ ] `README.md` updated with diagnostic and status entities table
- [ ] `CHANGELOG.md` updated
- [ ] Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write`

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | coordinator | `coordinator.py` | `feat(coordinator): track mode, commands, brightness, and light health` |
| 2 | sensor | `sensor.py`, `switch.py` | `feat(sensor): add mode, current brightness, and last command sensors with device info` |
| 3 | binary_sensor | `binary_sensor.py`, `__init__.py` | `feat(binary_sensor): add dim-to-warm, brightness curve, and problem binary sensors` |
| 4 | tests | `tests/test_coordinator.py`, `tests/test_init.py` | `test: add test coverage for diagnostic status entities and problem reporting` |
| 5 | docs | `README.md`, `CHANGELOG.md` | `docs: document status and diagnostic entities` |
| 6 | wrap-up | `tasks/3-feature-diagnostic-status-entities.md` | `chore: complete task #3` |

---

## Definition of done

- [ ] All work items checked off
- [ ] Security review passed
- [ ] Validation passes (`pytest` and `ruff` clean)
- [ ] Documentation updated
