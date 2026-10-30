# Task: studio live mode

**Task:** #8
**Status:** done
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Separate real-time hardware live modes for timeline/room curve simulation and dim-to-warm curve calibration
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

When tuning a room's 24-hour circadian schedule, room brightness distribution curves, or fixture dim-to-warm curves in the Scheduled Scenes Studio, visual color swatches on screen are only an approximation of how physical LED fixtures behave in the actual room.

This task introduces **Live Mode** to Scheduled Scenes Studio so that real physical lights in Home Assistant mirror the values shown in the Studio in real time as the user scrubs time, adjusts brightness, or drags curve control points.

Because configuring a **room's timeline / brightness distribution** and calibrating a **fixture's dim-to-warm curve** are two fundamentally different tasks, Live Mode is split into two **separate, mutually exclusive modes**:

1. **Timeline & Room Curve Live Mode (`room` mode):**
   - Drives all lights in the active room (`currentProgram.lights`) using the full room pipeline (`calculateFixtureOutput`: schedule interpolation at `scrubMinutes` + `liveRoomBrightness` override + Room Brightness Distribution Curves + Dim-to-Warm Curves).
   - Used when scrubbing through the 24-hour timeline, editing schedule checkpoints in `CircadianTimeline.vue`, testing room brightness overrides in `ScrubSimulator.vue`, or tuning **Room Brightness Distribution Curves** in `CurveEditor.vue`.
   - Dragging a control point `[roomBri, fixtureBri]` on a Room Brightness Distribution Curve automatically syncs `liveRoomBrightness` to `roomBri` so the room's physical lights preview that exact point on the curve.

2. **Dim-to-Warm Curve Calibration Live Mode (`dim_to_warm` mode):**
   - Drives only the fixtures assigned to the currently selected `DimToWarmCurve` (`activeCurve.lights`), completely independent of the room's time-of-day schedule or room brightness distribution curves.
   - Provides a dedicated **Fixture Test Brightness (`0–100%`)** slider in the Dim-to-Warm editor, sending `{ brightness_pct: testBrightness, color_temp_kelvin: evaluateDimToWarm(points, testBrightness) }` directly to the curve's lights.
   - Dragging a control point `[fixtureBri, kelvin]` on the Dim-to-Warm curve canvas automatically snaps the test brightness to `fixtureBri` so the user sees the exact physical brightness and warmth of the point being adjusted.

## Affected hosts

- `all` — Frontend studio (`web/src/services/liveOutputService.ts`, `web/src/App.vue`, `web/src/components/ScrubSimulator.vue`, `web/src/components/CurveEditor.vue`, `web/src/components/CircadianTimeline.vue`, `web/src/types.ts`).

---

## Work items

### 1. Live Output Service, Throttling & HA Transport
**Files:** `web/src/services/liveOutputService.ts`, `web/src/types.ts`

- [x] (auto) Define Live Mode types in `web/src/types.ts`:
  - `LiveModeType = 'off' | 'room' | 'dim_to_warm'`
  - `FixtureLiveTarget = { entityId: string; brightnessPct: number; kelvin?: number }`
  - `HAConnectionConfig = { url: string; token: string; resumeOnExit: boolean }`
- [x] (auto) Create `web/src/services/liveOutputService.ts` supporting three execution transports:
  - **HA Embedded Bridge:** Uses `window.hass.callService` / parent HA connection when running inside the Home Assistant sidebar panel.
  - **HA Remote REST/WebSocket Client:** Uses user-supplied Home Assistant URL + Long-Lived Access Token (persisted in `localStorage`) so standalone Studio sessions (`ahjo:5173`) can also control physical lights directly.
  - **Mock Simulation Transport:** Updates reactive mock light states and records dispatched payloads when testing offline.
- [x] (auto) Implement **throttling & state deduplication**:
  - Throttle outbound `light.turn_on` / `light.turn_off` calls (120ms trailing edge) to avoid flooding Zigbee/Thread/Wi-Fi bridges during 60fps mouse dragging.
  - Cache last-dispatched `{ brightnessPct, kelvin }` per `entity_id` and only send commands for fixtures whose target values changed.
  - Respect fixture capabilities from `entityService` (`supported_color_modes`, `min_color_temp_kelvin`, `max_color_temp_kelvin`), omitting `color_temp_kelvin` for dimmable-only lights and clamping Kelvin to supported bounds.
- [x] (auto) Implement **program pause & restore lifecycle**:
  - When either Live Mode starts, pause the corresponding `scheduled_scenes` program (`scheduled_scenes.disable`) so periodic background transitions or `enable_when_light_turn_on` triggers do not fight with Live Mode commands.
  - When Live Mode stops (or on `beforeunload`), optionally call `scheduled_scenes.resume_schedule` / `scheduled_scenes.enable` to return the room lights to normal scheduled operation.

### 2. Timeline & Room Curve Live Mode (`room` mode)
**Files:** `web/src/components/ScrubSimulator.vue`, `web/src/components/CurveEditor.vue`, `web/src/App.vue`

- [x] (auto) Add a **Live Room Mode** toggle button in `ScrubSimulator.vue` (and a status pill in the top header of `App.vue`):
  - Enabling `room` Live Mode automatically disables `dim_to_warm` Live Mode if active.
  - Display a pulsing live badge (`LIVE ROOM SYNC`) and per-fixture live output status on each fixture card in `ScrubSimulator.vue`.
- [x] (auto) Wire reactive room state changes to `liveOutputService`:
  - Watch `scrubMinutes`, `liveRoomBrightness`, `currentProgram.schedule`, `currentProgram.lights`, `config.brightness_curves`, and `config.curves` while `liveMode === 'room'`.
  - Compute each room fixture's output via `calculateFixtureOutput` and dispatch updates to `currentProgram.lights`.
- [x] (auto) Synchronize **Room Brightness Distribution Curve** editing with `room` Live Mode:
  - In `CurveEditor.vue` when `activeCategory === 'brightness'`, display a vertical playhead line at `liveRoomBrightness` on the 2D canvas and show a quick toggle for **Live Room Mode** right in the Brightness Curve header.
  - When the user drags a point `[x, y]` on a Room Brightness Distribution Curve, emit `update:roomBrightness(x)` to set `liveRoomBrightness = x` so the room immediately previews that exact curve point.

### 3. Dim-to-Warm Curve Calibration Live Mode (`dim_to_warm` mode)
**Files:** `web/src/components/CurveEditor.vue`, `web/src/App.vue`

- [x] (auto) Add a dedicated **Dim-to-Warm Live Calibration Panel** in `CurveEditor.vue` when `activeCategory === 'dim_to_warm'`:
  - **Live Dim-to-Warm Toggle** (`Live DTW Calibration`), mutually exclusive with `room` Live Mode.
  - **Fixture Test Brightness Slider (`0–100%`)** with a play/sweep button (`0% → 100%`) and live readout of the interpolated Kelvin (`evaluateDimToWarm(activeCurve.points, dtwTestBrightness)`) and color swatch.
  - **Visual Playhead on Canvas:** Render a vertical playhead line and indicator dot on the Dim-to-Warm 2D SVG graph at `dtwTestBrightness` showing the active `(brightness %, Kelvin)` operating point.
- [x] (auto) Auto-follow curve control points during dragging:
  - When the user clicks or drags a point `[x, y]` on the Dim-to-Warm curve canvas (or edits its X/Y number inputs), automatically update `dtwTestBrightness = x`.
  - While `liveMode === 'dim_to_warm'`, evaluate `evaluateDimToWarm(activeCurve.points, dtwTestBrightness)` and dispatch `{ brightnessPct: dtwTestBrightness, kelvin }` exclusively to `activeCurve.lights`.

### 4. Curve Fixture Assignment & HA Connection Controls
**Files:** `web/src/components/CurveEditor.vue`, `web/src/App.vue`

- [x] (auto) Add interactive fixture assignment chips in `CurveEditor.vue` so users can attach/detach lights (`activeCurve.lights`) to any Brightness or Dim-to-Warm curve before testing it in Live Mode.
- [x] (auto) Add a connection status & configuration modal/popover in `App.vue` header allowing standalone users to enter a Home Assistant URL and Long-Lived Access Token (or see active HA sidebar / Mock status) and configure "Resume schedule when exiting Live Mode".

---

## Security considerations

- Never hardcode or commit Home Assistant tokens or URLs in repository files.
- If a user configures a remote HA token in standalone dev mode, store it only in browser `localStorage` and never include it in exported YAML configurations.

---

## Out-of-repo changes

None.

---

## Validation

- [x] Enabling **Timeline & Room Curve Live Mode** dispatches throttled `light.turn_on` / `light.turn_off` calls for `currentProgram.lights` matching `ScrubSimulator` outputs when scrubbing time, adjusting room brightness, or dragging Room Brightness Distribution curve points.
- [x] Enabling **Dim-to-Warm Calibration Live Mode** automatically turns off Room Live Mode and dispatches `{ brightness_pct, color_temp_kelvin }` only to `activeCurve.lights` as the Fixture Test Brightness slider or Dim-to-Warm curve points are moved.
- [x] Turning off Live Mode restores schedule state when "Resume on exit" is enabled.
- [x] `pnpm --dir web build` compiles cleanly with zero TypeScript errors.

---

## Documentation updates

- [x] Update `README.md` with documentation on Studio Live Modes (Room/Timeline Simulation vs. Dim-to-Warm Calibration).
- [x] Update `TODO.md` via `node ~/dev/dev-tools/scripts/todo-status.mjs --write`.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | live-service | `web/src/types.ts`, `web/src/services/liveOutputService.ts` | `feat(web): add throttled live light output service with HA and mock transports` |
| 2 | live-modes | `web/src/App.vue`, `web/src/components/ScrubSimulator.vue`, `web/src/components/CurveEditor.vue` | `feat(web): add separate live modes for room timeline simulation and dim-to-warm calibration` |
| 3 | wrap-up | `tasks/done/8-feature-studio-live-mode-done.md`, `README.md`, `TODO.md` | `chore: mark task #8 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] Separate Live Modes verified for both Timeline/Room Curves and Dim-to-Warm Curves
- [x] Type checks and frontend build pass
- [x] Documentation updated
