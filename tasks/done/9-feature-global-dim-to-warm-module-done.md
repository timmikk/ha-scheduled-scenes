# Task: global dim to warm module

**Task:** #9
**Status:** done
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Global dim-to-warm curve module separated from room config with contextual room quick-edit
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

In physical installations, the same model of light fixture (e.g. Philips Hue GU10 spots, Ikea Trådfri E27 bulbs, or architectural warm-glow LED strips) is often installed across multiple rooms. Because a **Dim-to-Warm curve** models a physical hardware characteristic (`fixture_brightness % → color_temp_kelvin`), it is inherently **global** rather than room-specific.

Previously in the Studio (`App.vue` and `CurveEditor.vue`):
1. The Dim-to-Warm curve editor was embedded inside the active Room Configuration view as a secondary tab alongside Room Brightness Distribution Curves, making it appear room-scoped.
2. Users could not easily see at a glance which rooms/lights across the home share a Dim-to-Warm curve, nor was there a dedicated top-level place to manage global hardware curves independently of rooms.
3. Conversely, when configuring a room, there was no quick action on a room fixture chip or simulator card to inspect, assign, or tweak that light's global Dim-to-Warm curve in-place without scrolling and hunting through a curve dropdown.

This task separates Dim-to-Warm configuration into a standalone, reusable **Global Dim-to-Warm Module (`DimToWarmManager.vue`)** that can be:
- Opened **globally** via a top-level navigation view in `App.vue` (alongside Room tabs) to manage all hardware curve profiles and cross-room light assignments.
- Opened **contextually from Room Configuration** (as an inline expandable panel or modal drawer) by clicking a light's settings / DTW curve badge in `RoomLightManager.vue` or `ScrubSimulator.vue`, pre-selecting that light and its assigned curve for immediate editing.

## Architectural Recommendations Implemented

1. **Reusable `<DimToWarmManager>` Module with Two Presentation Modes:**
   - **Standalone Global View (`mode="page"`):** Accessible from the top header bar (`🌡️ Global Dim-to-Warm` tab next to the Room switcher). Shows a selector/list of all global curves (with badges indicating how many lights and rooms use each curve), a multi-room fixture assignment picker, the 2D SVG curve canvas, and Live DTW Calibration controls.
   - **Contextual Quick-Edit Modal (`mode="contextual"`, `:focus-light-id="entityId"`):** Triggered by clicking the DTW curve badge or `⚙️` button on any fixture in `RoomLightManager.vue` or `ScrubSimulator.vue`. Opens focused on `focusLightId`:
     - Lets the user switch which global curve `focusLightId` is assigned to (or `None`, or `+ Create New Curve for this light`, or `Fork/Clone Curve for this light` to customize without affecting other rooms).
     - Displays an explicit **Shared Curve Impact Banner** (e.g., *"Shared Hardware Profile: This curve is assigned to X fixtures across [Living Room, Kitchen]. Edits below apply globally to all of them."*).
     - Embeds the exact same interactive 2D SVG curve editor so points can be dragged immediately without leaving the room workflow.

2. **Dedicated Room Brightness Distribution Editor (`CurveEditor.vue`):**
   - Simplified `CurveEditor.vue` inside the Room Configuration view so it is exclusively responsible for **Room Brightness Distribution Curves** (`room_brightness % → fixture_brightness %`), scoped and filtered to the active room's fixtures (`currentProgram.lights`).

3. **Global-Only Dim-to-Warm Schema Normalization:**
   - In `YamlViewer.vue`, Dim-to-Warm `curves` are serialized at the top-level `scheduled_scenes.curves:` key. When importing legacy YAML with per-program `curves:`, they are automatically hoisted and merged into the global `config.curves` dictionary.

## Affected hosts

- `all` — Frontend studio (`web/src/components/DimToWarmManager.vue`, `web/src/components/CurveEditor.vue`, `web/src/components/RoomLightManager.vue`, `web/src/components/ScrubSimulator.vue`, `web/src/components/YamlViewer.vue`, `web/src/App.vue`, `web/src/mock/data.ts`).

---

## Work items

### 1. Reusable Global Dim-to-Warm Module (`DimToWarmManager.vue`)
**Files:** `web/src/components/DimToWarmManager.vue`, `web/src/mock/data.ts`

- [x] (auto) Create `DimToWarmManager.vue` encapsulating all Dim-to-Warm curve state and UI:
  - Props: `curves: Record<string, DimToWarmCurve>`, `programs: ProgramConfig[]`, `focusLightId?: string | null`, `mode?: 'page' | 'contextual'`.
  - Curve management: create, rename, duplicate/clone, and delete global Dim-to-Warm curves.
  - Cross-room usage metadata: compute and display which rooms (`programs`) and fixtures use each curve.
  - Interactive 2D SVG coordinate editor (`Fixture Brightness 0–100%` → `Color Temp 1800K–5000K`) with point dragging, double-click removal, and numeric fine-tuning inputs.
  - Multi-area fixture assignment selector allowing lights from any room/area to be attached or detached from the active curve.
- [x] (auto) Support **Contextual Quick-Edit Mode** (`focusLightId` prop):
  - Display a header bar for the focused fixture (`friendlyName` + `entity_id` + supported Kelvin range badge).
  - Provide a quick **Assigned Curve Selector** dropdown (`None / No DTW Curve`, existing global curves, `+ Create New Curve`, or `Fork/Clone Curve for this light`).
  - Show a warning/info pill when the selected curve is shared across multiple lights/rooms.
- [x] (auto) Update `INITIAL_CONFIG` in `web/src/mock/data.ts` with multi-room sample data (e.g. `living_room` and `kitchen` sharing a global `gu10_warm_glow` and `cove_ambient_led` curve) to demonstrate cross-room curve sharing out of the box.

### 2. Top-Level Navigation & Room-Scoped `CurveEditor.vue` Refactor
**Files:** `web/src/App.vue`, `web/src/components/CurveEditor.vue`

- [x] (auto) Add a top-level view switcher in `App.vue` header:
  - Room tabs (`🛋️ living_room`, `🛋️ kitchen`, `+ Add Room`) switch `activeView = 'room'` and select the room.
  - Dedicated global button **`🌡️ Global Dim-to-Warm`** (with count badge) switches `activeView = 'dim_to_warm'` to show the full-page `<DimToWarmManager mode="page" />`.
- [x] (auto) Refactor `CurveEditor.vue` to focus exclusively on **Room Brightness Distribution Curves** for the active room:
  - Remove the `Dim-to-Warm Curves` category tab from `CurveEditor.vue` (replaced with a link/button `"🌡️ Dim-to-Warm Curves →"` that opens the DTW module).
  - Filter or highlight brightness curves relevant to `currentProgram.lights` and allow assigning lights from `currentProgram.lights`.

### 3. Contextual Quick-Access from Room Configuration (`RoomLightManager` & `ScrubSimulator`)
**Files:** `web/src/components/RoomLightManager.vue`, `web/src/components/ScrubSimulator.vue`, `web/src/App.vue`

- [x] (auto) In `RoomLightManager.vue`:
  - Show each fixture's currently assigned global Dim-to-Warm curve badge (`🌡️ <name>` or `+ DTW`) on its chip, plus a settings button (`⚙️`).
  - Clicking the badge/button emits `@open-light-dtw="entityId"`.
- [x] (auto) In `ScrubSimulator.vue`:
  - Make the Dim-to-Warm curve badge on each fixture card interactive (clickable button: `🌡️ {{ fix.dimToWarmCurveName || '+ DTW' }}`), emitting `@open-light-dtw="fix.lightId"`.
- [x] (auto) In `App.vue`:
  - Handle `@open-light-dtw` by opening `<DimToWarmManager mode="contextual" :focus-light-id="contextualLightId" />` in a backdrop modal overlay (with a `"↗ Full View"` button to transition to full page).

### 4. Global YAML Normalization
**Files:** `web/src/components/YamlViewer.vue`

- [x] (auto) Ensure `YamlViewer.vue` always exports `curves` at the top-level `scheduled_scenes.curves` key and imports any legacy per-program `curves` by merging them into the global `config.curves` store.

---

## Security considerations

None — Pure client-side UI restructuring and configuration state management.

---

## Out-of-repo changes

None.

---

## Validation

- [x] Top navigation bar switches cleanly between Room configurations and the Global **Dim-to-Warm Curves** module.
- [x] Modifying a global Dim-to-Warm curve updates calculated temperatures across all rooms that have fixtures assigned to that curve.
- [x] Clicking a fixture's DTW badge/settings in `RoomLightManager` or `ScrubSimulator` opens the contextual `<DimToWarmManager>` focused on that fixture, allowing instant curve assignment or curve point editing.
- [x] `CurveEditor.vue` in the room view cleanly manages Room Brightness Distribution Curves without duplicating Dim-to-Warm tabs.
- [x] `pnpm --dir web build` compiles with zero TypeScript or Vue template errors.
- [x] Pytest suite passes 53/53 tests cleanly.

---

## Documentation updates

- [x] Update `README.md` to describe the Global Dim-to-Warm Module and contextual quick-edit workflow in the Studio.
- [x] Update `TODO.md` via `node ~/dev/dev-tools/scripts/todo-status.mjs --write`.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | dtw-module | `web/src/components/DimToWarmManager.vue`, `web/src/mock/data.ts` | `feat(web): add standalone and contextual global DimToWarmManager module` |
| 2 | studio-ui | `web/src/App.vue`, `web/src/components/CurveEditor.vue`, `web/src/components/RoomLightManager.vue`, `web/src/components/ScrubSimulator.vue`, `web/src/components/YamlViewer.vue` | `feat(web): separate global dim-to-warm view from room config and add fixture quick-edit` |
| 3 | wrap-up | `tasks/done/9-feature-global-dim-to-warm-module-done.md`, `README.md`, `TODO.md` | `chore: mark task #9 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] Global view and room-level contextual quick-edit verified
- [x] Frontend build passes cleanly
- [x] Pytest test suite passes cleanly (53/53 passed)
- [x] Documentation updated
