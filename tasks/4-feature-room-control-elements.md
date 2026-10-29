# Task: room control elements

**Task:** #4
**Status:** pending
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** high
**Category:** Features
**Summary:** Add room control elements: virtual light entity with brightness/temp controls and schedule brightness offset
**Host:** all
**Created:** 2026-10-29

## Context

`ha-scheduled-scenes` manages dynamic circadian curves, room brightness distribution, and automated transitions across Home Assistant light fixtures. Currently, users have a master schedule switch (`switch.schedule_<room>`) and status/diagnostic sensors, but lack a native, high-level control entity for driving the room from Home Assistant dashboards, voice assistants, and wall buttons.

To provide an intuitive and unified control surface, this feature introduces:
1. **Virtual Room Light Entity (`light.<room>`):**
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

- [ ] (auto) Add `brightness_offset: int = 0` (clamped to `-50` to `50`) to `ScheduledSceneProgram`.
- [ ] (auto) Add `manual_color_temp: int | None = None` to `ScheduledSceneProgram`.
- [ ] (auto) Update `async_transition()` to apply `self.brightness_offset` to target schedule brightness before distributing to lights, clamping effective room brightness to `0-100%`.
- [ ] (auto) Update `async_adjust_brightness()` and `calculate_manual_light_state()`:
  - Support passing optional `color_temp: int | None`.
  - When a fixture has no dim-to-warm curve, preserve `self.manual_color_temp` if set; otherwise use the current active schedule transition's Kelvin rather than a static default.
- [ ] (auto) Implement `async_set_brightness_offset(offset: int)` updating `self.brightness_offset`, recording command history, and immediately triggering `async_transition()` if in `auto` mode.
- [ ] (auto) Implement `async_set_manual_color_temp(kelvin: int | None)` updating `self.manual_color_temp`, switching mode to `manual`, and updating active lights.
- [ ] (auto) Ensure `async_turn_on()` clears both `manual_brightness` and `manual_color_temp`, re-enables `auto` mode, and applies scheduled transition.
- [ ] (auto) Ensure `async_turn_off()` clears overrides and dispatches `turn_off` to lights.
- [ ] (auto) Ensure `async_resume_schedule()` clears `manual_color_temp` alongside `manual_brightness`.

### 2. Virtual Light Entity Platform
**Files:** `custom_components/scheduled_scenes/light.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (HA light platform)

Implement the room virtual light entity exposing native Home Assistant light controls.

- [ ] (auto) Register `Platform.LIGHT` in `PLATFORMS` in `custom_components/scheduled_scenes/__init__.py`.
- [ ] (auto) Create `custom_components/scheduled_scenes/light.py` with `async_setup_entry`.
- [ ] (auto) Implement `ScheduledSceneLight(LightEntity)` attached to `DeviceInfo((DOMAIN, entry_id))`.
- [ ] (auto) Configure supported color modes: `{ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS}` with `min_color_temp_kelvin` (2000K) and `max_color_temp_kelvin` (6500K).
- [ ] (auto) Implement `is_on` reflecting `program.is_any_light_on()`.
- [ ] (auto) Implement `brightness` reflecting `program.get_current_room_brightness()` scaled to `0-255`.
- [ ] (auto) Implement `color_temp_kelvin` reflecting current effective color temperature.
- [ ] (auto) Implement `async_turn_on(**kwargs)`:
  - If called with no brightness/temp kwargs: call `program.async_turn_on()` (resumes `auto` mode with schedule).
  - If called with `ATTR_BRIGHTNESS`: convert to `0-100%` and call `program.async_adjust_brightness(brightness=pct)`.
  - If called with `ATTR_COLOR_TEMP_KELVIN`: call `program.async_set_manual_color_temp(kelvin)`.
- [ ] (auto) Implement `async_turn_off(**kwargs)` calling `program.async_turn_off()`.
- [ ] (auto) Subscribe to coordinator state changes via `program.async_add_listener(self.async_write_ha_state)`.

### 3. Number Platform (Brightness Offset)
**Files:** `custom_components/scheduled_scenes/number.py`, `custom_components/scheduled_scenes/__init__.py`
**Host impact:** None (HA number platform)

Implement the room brightness offset slider entity.

- [ ] (auto) Register `Platform.NUMBER` in `PLATFORMS` in `custom_components/scheduled_scenes/__init__.py`.
- [ ] (auto) Create `custom_components/scheduled_scenes/number.py` with `async_setup_entry`.
- [ ] (auto) Implement `ScheduledSceneBrightnessOffsetNumber(NumberEntity)` attached to `DeviceInfo((DOMAIN, entry_id))`.
- [ ] (auto) Configure slider attributes: `native_min_value = -50`, `native_max_value = 50`, `native_step = 1`, `mode = NumberMode.SLIDER`, `native_unit_of_measurement = "%"`.
- [ ] (auto) Implement `native_value` returning `program.brightness_offset`.
- [ ] (auto) Implement `async_set_native_value(value: float)` calling `program.async_set_brightness_offset(int(value))`.
- [ ] (auto) Subscribe to coordinator state changes via `program.async_add_listener(self.async_write_ha_state)`.

### 4. Automated Tests & Validation
**Files:** `tests/test_light.py`, `tests/test_number.py`, `tests/test_coordinator.py`, `tests/test_init.py`
**Host impact:** None (pytest suite)

Add comprehensive tests for virtual light operations, brightness offset calculations, and platform setup.

- [ ] (auto) Test virtual light `turn_on` resumes `auto` mode and restores schedule values.
- [ ] (auto) Test virtual light `turn_off` turns off fixtures and switches mode to `auto-off`.
- [ ] (auto) Test virtual light brightness adjustment sets `manual` mode and updates fixture brightness.
- [ ] (auto) Test brightness adjustment without dim-to-warm preserves active schedule Kelvin.
- [ ] (auto) Test virtual light color temperature override.
- [ ] (auto) Test number slider adjusts brightness offset and affects active transitions in `auto` mode.
- [ ] (auto) Verify all new entities are registered in `PLATFORMS` and linked to the room device registry entry.

### 5. Documentation & Changelog
**Files:** `README.md`, `CHANGELOG.md`
**Host impact:** None (documentation)

- [ ] (auto) Document `light.<room>` and `number.<room>_brightness_offset` in `README.md` under Entities and Interactive Control.
- [ ] (auto) Update `CHANGELOG.md` with features and usage details.
