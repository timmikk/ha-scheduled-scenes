# Task: room control elements

**Task:** #4
**Status:** done
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** high
**Category:** Features
**Summary:** Add room control elements: virtual light entity with brightness/temp controls and schedule brightness offset
**Host:** all
**Created:** 2026-10-29
**Completed:** 2026-10-29

## Context

`ha-scheduled-scenes` manages dynamic circadian curves, room brightness distribution, and automated transitions across Home Assistant light fixtures. Currently, users have a master schedule switch (`switch.schedule_<room>`) and status/diagnostic sensors, but lack a native, high-level control entity for driving the room from Home Assistant dashboards, voice assistants, and wall buttons.

To provide an intuitive and unified control surface, this feature introduces:
1. **Virtual Room Light Entity (`light.<room>_lights`):**
   - **On / Off Toggle:** Turning on enables `auto` mode, clears manual overrides, and immediately transitions lights to current scheduled brightness and color temperature. Turning off turns off room fixtures and enters `auto-off` standby.
   - **Brightness Slider:** Adjusting brightness sets a manual room brightness percentage, pauses periodic schedule updates (switches mode to `manual`), and distributes brightness across fixtures. When dim-to-warm is enabled, lights warm/cool along configured curves; when dim-to-warm is disabled, lights retain the active scheduled Kelvin instead of falling back to a hardcoded 2700K.
   - **Color Temperature Control:** Directly adjust room color temperature in Kelvin on the light entity, overriding schedule/curve Kelvin until the light is toggled or reset back to `auto`.
2. **Schedule Brightness Offset Slider (`number.<room>_brightness_offset`):**
   - Slider from `-50%` to `+50%` (default `0%`) that nudges the entire 24-hour schedule curve up or down.
   - Allows adapting to dark rainy days or bright sunny seasons without leaving `auto` mode or editing YAML/config flow checkpoints.
3. **Unified Device Integration:**
   - Both the virtual light entity and brightness offset slider are registered under the existing room `DeviceInfo`, appearing alongside the schedule switch and diagnostic sensors under Settings -> Devices & Services.

## Affected hosts

- `all` — Custom component platforms (`light.py`, `number.py`), runtime coordinator (`coordinator.py`, `logic.py`), component registry (`__init__.py`), and automated test suites in `tests/`.

---

## Work items

### 1. Coordinator State & Control Logic
**Files:** `custom_components/scheduled_scenes/coordinator.py`, `custom_components/scheduled_scenes/logic.py`
**Host impact:** None (component runtime logic)

Extend `ScheduledSceneProgram` to support manual color temperature override, schedule brightness offset, and preserve scheduled Kelvin when dim-to-warm is disabled.

- [x] (auto) Add `brightness_offset: int = 0` (clamped to `-50` to `50`) to `ScheduledSceneProgram`.
- [x] (auto) Add `manual_color_temp: int | None = None` to `ScheduledSceneProgram`.
- [x] (auto) Update `async_transition()` to apply `self.brightness_offset` to target schedule brightness before distributing to lights, clamping effective room brightness to `0-100%`.
- [x] (auto) Update `async_adjust_brightness()` and `calculate_manual_light_state()`:
  - Support passing optional `color_temp: int | None`.
  - When a fixture has no dim-to-warm curve, preserve `self.manual_color_temp` if set; otherwise use the current active schedule transition's Kelvin rather than a static default.
- [x] (auto) Implement `async_set_brightness_offset(offset: int)` updating `self.brightness_offset`, recording command history, and immediately triggering `async_transition()` if in `auto` mode.
- [x] (auto) Implement `async_set_manual_color_temp(kelvin: int | None)` updating `self.manual_color_temp`, switching mode to `manual`, and updating active lights.
- [x] (auto) Ensure `async_turn_on()` clears both `manual_brightness` and `manual_color_temp`, re-enables `auto` mode, and applies scheduled transition.
- [x] (auto) Ensure `async_turn_off()` clears overrides and dispatches `turn_off` to lights.
- [x] (auto) Ensure `async_resume_schedule()` clears `manual_color_temp` alongside `manual_brightness`.

### 2. Virtual Light Entity Platform
**Files:** `custom_components/scheduled_scenes/light.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (HA light platform)

Implement the room virtual light entity exposing native Home Assistant light controls.

- [x] (auto) Register `Platform.LIGHT` in `PLATFORMS` in `custom_components/scheduled_scenes/__init__.py`.
- [x] (auto) Create `custom_components/scheduled_scenes/light.py` with `async_setup_entry`.
- [x] (auto) Implement `ScheduledSceneLight(LightEntity)` attached to `DeviceInfo((DOMAIN, entry_id))`.
- [x] (auto) Configure supported color modes: `{ColorMode.COLOR_TEMP}` with `min_color_temp_kelvin` (2000K) and `max_color_temp_kelvin` (6500K).
- [x] (auto) Implement `is_on` reflecting `program.is_any_light_on()`.
- [x] (auto) Implement `brightness` reflecting `program.get_current_room_brightness()` scaled to `0-255`.
- [x] (auto) Implement `color_temp_kelvin` reflecting current effective color temperature.
- [x] (auto) Implement `async_turn_on(**kwargs)`:
  - If called with no brightness/temp kwargs: call `program.async_turn_on()` (resumes `auto` mode with schedule).
  - If called with `ATTR_BRIGHTNESS`: convert to `0-100%` and call `program.async_adjust_brightness(brightness=pct)`.
  - If called with `ATTR_COLOR_TEMP_KELVIN`: call `program.async_set_manual_color_temp(kelvin)`.
- [x] (auto) Implement `async_turn_off(**kwargs)` calling `program.async_turn_off()`.
- [x] (auto) Subscribe to coordinator state changes via `program.async_add_listener(self.async_write_ha_state)`.

### 3. Number Platform (Brightness Offset)
**Files:** `custom_components/scheduled_scenes/number.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (HA number platform)

Implement the room brightness offset slider entity.

- [x] (auto) Register `Platform.NUMBER` in `PLATFORMS` in `custom_components/scheduled_scenes/__init__.py`.
- [x] (auto) Create `custom_components/scheduled_scenes/number.py` with `async_setup_entry`.
- [x] (auto) Implement `ScheduledSceneBrightnessOffsetNumber(NumberEntity)` attached to `DeviceInfo((DOMAIN, entry_id))`.
- [x] (auto) Configure slider attributes: `native_min_value = -50`, `native_max_value = 50`, `native_step = 1`, `mode = NumberMode.SLIDER`, `native_unit_of_measurement = "%"`.
- [x] (auto) Implement `native_value` returning `program.brightness_offset`.
- [x] (auto) Implement `async_set_native_value(value: float)` calling `program.async_set_brightness_offset(int(value))`.
- [x] (auto) Subscribe to coordinator state changes via `program.async_add_listener(self.async_write_ha_state)`.

### 4. Automated Tests & Validation
**Files:** `tests/test_light.py`, `tests/test_number.py`, `tests/test_coordinator.py`, `tests/test_init.py`
**Host impact:** None (pytest suite)

Add comprehensive tests for virtual light operations, brightness offset calculations, and platform setup.

- [x] (auto) Test virtual light `turn_on` resumes `auto` mode and restores schedule values.
- [x] (auto) Test virtual light `turn_off` turns off fixtures and switches mode to `auto-off`.
- [x] (auto) Test virtual light brightness adjustment sets `manual` mode and updates fixture brightness.
- [x] (auto) Test brightness adjustment without dim-to-warm preserves active schedule Kelvin.
- [x] (auto) Test virtual light color temperature override.
- [x] (auto) Test number slider adjusts brightness offset and affects active transitions in `auto` mode.
- [x] (auto) Verify all new entities are registered in `PLATFORMS` and linked to the room device registry entry.

### 5. Documentation & Changelog
**Files:** `README.md`, `CHANGELOG.md`
**Host impact:** None (documentation)

- [x] (auto) Document `light.<room>_lights` and `number.<room>_brightness_offset` in `README.md` under Entities and Interactive Control.
- [x] (auto) Update `CHANGELOG.md` with features and usage details.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | coordinator | `coordinator.py`, `logic.py` | `feat(coordinator): support manual color temperature and schedule brightness offset` |
| 2 | light | `light.py`, `__init__.py`, `binary_sensor.py`, `sensor.py`, `switch.py`, `config_flow.py` | `feat(light): add room virtual light entity with brightness and kelvin controls` |
| 3 | number | `number.py` | `feat(number): add schedule brightness offset slider entity` |
| 4 | tests | `tests/test_light.py`, `tests/test_number.py`, `tests/test_coordinator.py`, `tests/test_init.py`, `tests/test_logic.py`, `tests/test_parity.py`, `tests/test_config_flow.py`, `.gitignore` | `test: add test coverage for virtual light and brightness offset entities` |
| 5 | docs | `README.md`, `CHANGELOG.md` | `docs: document room virtual light entity and brightness offset slider` |
| 6 | wrap-up | `tasks/4-feature-room-control-elements.md` | `chore: mark task #4 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] Code review passed
- [x] Validation passes (53 pytest unit/integration tests pass with 93% coverage, ruff clean)
- [x] Documentation and changelog updated

---

## Execution log

- 2026-10-29: Initialized worktree at `.dev/worktree/4-feature-room-control-elements` on branch `feature/4-room-control-elements`.
- 2026-10-29: Extended `ScheduledSceneProgram` in `coordinator.py` and calculation logic in `logic.py` with `brightness_offset`, `manual_color_temp`, and fallback to scheduled Kelvin when dim-to-warm curves are disabled. Committed `656f97c`.
- 2026-10-29: Implemented `ScheduledSceneLight` in `custom_components/scheduled_scenes/light.py` exposing `light.<room>_lights` with `ColorMode.COLOR_TEMP`, brightness, and Kelvin controls registered under the room `DeviceInfo`. Committed `2d636a6`.
- 2026-10-29: Implemented `ScheduledSceneBrightnessOffsetNumber` in `custom_components/scheduled_scenes/number.py` exposing `number.<room>_brightness_offset` (-50% to +50%) with real-time transition updates. Committed `15084ba`.
- 2026-10-29: Added comprehensive test suites in `tests/test_light.py` and `tests/test_number.py`, updated coordinator and logic tests, achieving 53 passing tests and 93% code coverage. Committed `f7cbb09`.
- 2026-10-29: Documented control entities and usage in `README.md` and `CHANGELOG.md`. Committed `0695a84`.

---

## Outcome

Successfully added native room control entities to the `ha-scheduled-scenes` integration:
1. **Virtual Room Light Entity (`light.<room>_lights`):**
   - Provides native HA brightness and Kelvin sliders for the entire room.
   - Turning on clears manual overrides and returns to `auto` mode applying the circadian curve. Turning off turns off room fixtures and enters `auto-off` mode.
   - Setting manual brightness retains the active scheduled Kelvin when dim-to-warm curves are omitted instead of falling back to a hardcoded 2700K.
   - Setting color temperature overrides the room Kelvin until toggled or resumed.
2. **Schedule Brightness Offset Slider (`number.<room>_brightness_offset`):**
   - Allows users to shift the baseline room brightness up or down by -50% to +50% without leaving `auto` mode or editing schedules.
3. **53 Automated Tests & 93% Coverage:**
   - Full test coverage across turn on/off, manual brightness, dim-to-warm interaction, Kelvin overrides, and offset adjustments.

---

## Actual commits

- 656f97c feat(coordinator): support manual color temperature and schedule brightness offset
- 2d636a6 feat(light): add room virtual light entity with brightness and kelvin controls
- 15084ba feat(number): add schedule brightness offset slider entity
- f7cbb09 test: add test coverage for virtual light and brightness offset entities
- 0695a84 docs: document room virtual light entity and brightness offset slider
