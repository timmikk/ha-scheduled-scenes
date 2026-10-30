# Task: dynamic sun timeline curve points

**Task:** #18
**Status:** pending
**Type:** feature
**Complexity:** large
**Mode:** auto
**Priority:** high
**Category:** Features
**Summary:** Support dynamic timeline curve points fixed to sun events and elevation angles with yearly variation visualization, seasonal simulator scrubbing, and deterministic overlap handling
**Host:** all
**Created:** 2026-10-30
**Completed:** —

## Context

In Home Assistant circadian lighting, static 24-hour schedules (e.g., fixed brightness transitions at 07:00, 18:00, 22:00) fail to adapt to natural seasonal shifts. Depending on geographic latitude, sunrise and sunset vary significantly throughout the year (e.g. sunrise shifting between 04:30 in summer and 09:15 in winter). Homeowners need lighting curves whose transition checkpoints anchor to real-world solar events (such as sunrise, sunset, solar noon, dawn, dusk, or specific solar elevation angles like +10° or -6°) with configurable time or angle offsets.

Furthermore, future expansion will introduce additional dynamic point sources, such as ambient light sensors triggering transitions dynamically within target time windows when natural daylight drops.

This task introduces complete dynamic point support across Scheduled Scenes:
1. **Extensible Dynamic Point Data Model:** Generic schema architecture allowing schedule checkpoints to be static (`time: "HH:MM"`) or dynamic (`dynamic: { type: "sun" | "sensor", ... }`).
2. **Solar Calculation Engine (Python & TypeScript Parity):** Pure astronomical solar calculation algorithms (NOAA solar formulas) computing exact event times, elevation angle crossings, and angle-to-time conversions without hard runtime dependencies.
3. **Flexible Offsets (Time & Angle):** Offset capability supporting either duration (`HH:MM` / minutes, e.g. `+00:30` after sunrise) or solar elevation angle (degrees, e.g. `+5°` above horizon).
4. **Config Studio Point Configuration & Yearly Variation Visualization:**
   - Interactive checkpoint inspector/modal to configure static vs dynamic points, sun events, elevation angles, and offsets.
   - Distinctive visual styling for dynamic nodes (sun marker/halo).
   - Visualizing the seasonal time range over the year on the 24h timeline canvas (horizontal variation envelope/range brackets showing min/max drift across the year).
5. **Seasonal Scrubbing Simulator:**
   - Date / season selector in `ScrubSimulator.vue` (day of year slider 1–365, date picker, seasonal solstice/equinox presets).
   - Real-time recalculation of dynamic checkpoint positions as the simulated date changes.
6. **Deterministic Overlap & Collision Handling:**
   - Robust, deterministic resolution when seasonal horizontal movement causes points to overlap, cross, or collide with static or other dynamic points.
7. **Home Assistant Coordinator Integration:**
   - Dynamic schedule resolution in `coordinator.py` using Home Assistant's geographic coordinates (`hass.config.latitude`, `hass.config.longitude`) and solar events.

## Affected hosts

- `all` — Python component files in `custom_components/scheduled_scenes/` (`logic.py`, `coordinator.py`, new `solar.py`, and test suites in `tests/`) and Frontend studio files in `web/src/` (`types.ts`, `components/CircadianTimeline.vue`, `components/ScrubSimulator.vue`, `utils/solar.ts`, `utils/interpolator.ts`, and test suites).

---

## Work items

### 1. Extensible Dynamic Point Data Model & Pure Solar Engine
**Files:** `web/src/types.ts`, `web/src/utils/solar.ts`, `web/src/utils/solar.test.ts`, `custom_components/scheduled_scenes/solar.py`, `tests/test_solar.py`

- [ ] (auto) Define dynamic point schema in `web/src/types.ts` and `custom_components/scheduled_scenes/logic.py`:
  - `DynamicPointSourceType`: `'sun' | 'sensor'` (designed for easy future extension).
  - `SunEvent`: `'sunrise' | 'sunset' | 'solar_noon' | 'solar_midnight' | 'dawn' | 'dusk' | 'elevation'`.
  - `OffsetUnit`: `'time' | 'angle'`.
  - `DynamicPointConfig`:
    - `type: DynamicPointSourceType`
    - `event?: SunEvent`
    - `elevation?: number` (target elevation angle in degrees for `elevation` event)
    - `direction?: 'rising' | 'setting' | 'any'`
    - `offset_value?: number` (numeric offset in minutes or degrees)
    - `offset_unit?: OffsetUnit` (`'time'` or `'angle'`)
    - `overlap_priority?: number` (optional priority score, default 0)
  - Extend `ScheduleStep` with optional `dynamic?: DynamicPointConfig`.
- [ ] (auto) Implement pure solar calculation engine in `web/src/utils/solar.ts`:
  - Calculate solar declination, equation of time, solar noon, sunrise, sunset, dawn (-6° civil dawn), and dusk (-6° civil dusk) given latitude, longitude, and date.
  - Calculate exact time when solar elevation crosses a specific angle (rising or setting).
  - Convert angle offset (degrees) into effective time delta or target elevation.
  - Calculate yearly variation range `[minMinute, maxMinute]` across all 365 days of the year for any dynamic point.
- [ ] (auto) Implement matching Python solar calculation engine in `custom_components/scheduled_scenes/solar.py` ensuring exact cross-engine parity.
- [ ] (auto) Add comprehensive test suites (`solar.test.ts` and `test_solar.py`) testing solstices, equinoxes, elevation angle crossings, polar day/night fallbacks, and offset conversions.

### 2. Deterministic Point Overlap & Collision Resolution Engine
**Files:** `web/src/utils/interpolator.ts`, `web/src/utils/interpolator.test.ts`, `custom_components/scheduled_scenes/logic.py`, `tests/test_logic.py`

- [ ] (auto) Implement `resolveDynamicSchedule(steps: ScheduleStep[], date: Date, lat: number, lon: number): ResolvedScheduleStep[]`:
  - Evaluates dynamic points for the given date, resolving dynamic definitions into concrete `time` values (minutes of day).
  - Preserves static points as configured.
- [ ] (auto) Implement deterministic overlap and collision handling:
  - **Chronological Sorting:** Order all resolved steps monotonically by effective time of day.
  - **Collision Deduplication:** If two steps fall within the collision threshold ($\le 1$ minute):
    - Higher `overlap_priority` takes precedence.
    - If priorities are equal, dynamic points take precedence over static points.
    - Suppress/ignore the overshadowed point to prevent zero-duration transition anomalies or vertical mathematical ambiguity.
  - **Crossing / Inversion Safety:** When seasonal shifts cause a dynamic point to cross adjacent points, maintaining strict chronological order ensures continuous, valid piecewise interpolation.
- [ ] (auto) Add unit tests for overlap edge cases:
  - Dynamic sunset shifting before an afternoon static checkpoint.
  - Two dynamic points converging at the same minute.
  - High latitude extreme cases (e.g. sunset occurring in early afternoon in midwinter).

### 3. Config Studio Checkpoint Inspector & Dynamic Editor
**Files:** `web/src/components/CircadianTimeline.vue`, `web/src/components/CircadianTimeline.test.ts`

- [ ] (auto) Enhance selected checkpoint editor in `CircadianTimeline.vue`:
  - Point type selector: toggle between `Fixed Time` and `Dynamic (Sun)`.
  - When Dynamic is active:
    - Dynamic Source dropdown (defaults to "Sun", structured with provider registry pattern for future sensor inputs).
    - Sun Event selector: `Sunrise`, `Sunset`, `Solar Noon`, `Dawn (Civil)`, `Dusk (Civil)`, `Sun Elevation Angle`.
    - If `Sun Elevation Angle` is selected: angle input (-90° to +90°) and direction toggle (`Rising` / `Setting`).
    - Offset inputs:
      - Offset value (`+` / `-` numeric value).
      - Offset unit toggle: `Time (HH:MM / minutes)` vs `Angle (degrees)`.
    - Live feedback card showing:
      - Resolved time for the currently selected simulation date.
      - Yearly drift summary (e.g. "Yearly range: 04:32 (Jun) – 09:15 (Dec)").
- [ ] (auto) Add unit tests verifying checkpoint inspector switching between fixed and dynamic mode, changing sun events, and updating step definitions.

### 4. Config Studio Canvas Yearly Variation Visualization
**Files:** `web/src/components/CircadianTimeline.vue`

- [ ] (auto) Visual differentiation for dynamic nodes on the SVG canvas:
  - Dynamic checkpoints rendered with distinct border/ring, sun icon badge, or distinct theme color.
- [ ] (auto) Yearly variation envelope on the timeline graph:
  - For each dynamic step, compute `[minMinute, maxMinute]` across the year.
  - Render a subtle seasonal range bracket / shaded horizontal band / dotted guide line spanning from `scaleX(minMinute)` to `scaleX(maxMinute)` along the curve.
  - Interactive tooltip on hover showing seasonal variation details and solar parameters.
- [ ] (auto) Visual collision warning/indicator if points overlap on the active simulation date.

### 5. Simulator Seasonal Scrubbing & Real-Time Recalculation
**Files:** `web/src/components/ScrubSimulator.vue`, `web/src/components/ScrubSimulator.test.ts`, `web/src/App.vue`

- [ ] (auto) Add "Simulate Time of Year" control group to `ScrubSimulator.vue`:
  - Date / season slider: Day of year (1 to 365) with formatted date display (e.g. "Jun 21 - Summer Solstice").
  - Quick seasonal preset buttons: `Summer Solstice`, `Winter Solstice`, `Spring Equinox`, `Autumn Equinox`, `Today`.
- [ ] (auto) Integrate reactive dynamic schedule resolution into simulator state:
  - Dynamically resolved schedule steps update in real time as the season slider moves.
  - 24-hour playhead and time scrubber interactively interpolate against the season-adjusted curve.
  - Output levels and fixture states in the simulator preview update dynamically based on the active seasonal curve.
- [ ] (auto) Add unit tests in `ScrubSimulator.test.ts` verifying date scrubbing updates fixture calculations when dynamic points are present.

### 6. Home Assistant Coordinator & Runtime Integration
**Files:** `custom_components/scheduled_scenes/coordinator.py`, `custom_components/scheduled_scenes/logic.py`, `tests/test_coordinator.py`

- [ ] (auto) Enhance `ScheduledSceneProgram` in `coordinator.py`:
  - Retrieve latitude/longitude from `hass.config.latitude`, `hass.config.longitude`.
  - Maintain resolved daily schedule: compute dynamic schedule at startup and refresh daily at midnight or when solar events occur.
  - Use resolved dynamic schedule during `resolve_active_transition`.
  - Safely handle coordinates missing or polar day/night scenarios with documented fallbacks.
- [ ] (auto) Add integration tests in `test_coordinator.py` validating dynamic schedule resolution across day boundaries and seasonal updates.

### 7. Parity, Build & End-to-End Validation
**Files:** `tests/test_parity.py`, `web/`

- [ ] (auto) Add golden parity tests in `tests/test_parity.py` comparing Python `solar.py` and TypeScript `solar.ts` calculations across multiple latitudes and dates.
- [ ] (auto) Run `pnpm --dir web run test:run` to ensure all frontend unit and component tests pass.
- [ ] (auto) Run `pnpm --dir web run build` to verify clean TypeScript compilation and asset packaging.
- [ ] (auto) Run `pytest` to ensure all backend unit and coordinator tests pass cleanly.
