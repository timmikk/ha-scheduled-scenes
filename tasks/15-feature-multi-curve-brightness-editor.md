# Task: multi curve brightness editor

**Task:** #15
**Status:** pending
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Allow viewing and editing multiple room brightness distribution curves simultaneously with toggle visibility selector
**Host:** all
**Created:** 2026-10-30
**Completed:** —

## Context

In Scheduled Scenes Studio, the **Room Brightness Distribution Curves** editor (`CurveEditor.vue`) currently only displays and edits one curve at a time via a single dropdown selector. In real-world multi-fixture rooms (e.g. ambient cove LED strips, direct task downlights, floor accent lamps), fixtures operate along distinct brightness distribution profiles that work together as room brightness transitions from 0% to 100%.

Users need the ability to view and compare multiple curves on the coordinate canvas simultaneously (e.g. to ensure that cove lighting ramps up before task downlights turn on), easily toggle visibility of individual curves, and switch active editing focus between curves seamlessly.

This task enhances `CurveEditor.vue` to support:
1. **Multi-Curve Visibility Toggle Selector:** A multi-toggle curve selector and legend allowing users to toggle individual curves visible/hidden, with quick actions ("All", "None", "Room Only").
2. **Distinct Multi-Curve Color Palette:** Each curve is assigned a distinct color (Indigo, Emerald, Amber, Cyan, Rose, Purple, etc.) with matching canvas lines, gradients, and legend chips.
3. **Multi-Curve Canvas Rendering & Interaction:** Overlay all visible curves on the 2D coordinate SVG canvas simultaneously. Active curve has interactive drag points and shaded area; inactive visible curves are rendered as reference lines and can be clicked to activate.
4. **Active Curve Inspector & Fine Tuning:** Detailed fixture assignment and numeric point fine-tuning table for the focused curve, with quick switching between visible curves.
5. **Interactive Live Room Brightness Reference Cursor:** Optional vertical scrubber indicator on the canvas displaying where current room brightness intersects each visible curve.

## Affected hosts

- `all` — Frontend studio files in `web/src/` (`components/CurveEditor.vue`, `components/CurveEditor.test.ts`, and optionally `App.vue`).

---

## Work items

### 1. Multi-Curve State & Color Palette Management
**Files:** `web/src/components/CurveEditor.vue`, `web/src/types.ts`

- [ ] (auto) Define a distinct color palette constant (e.g., 8 accessible colors with stroke & gradient values) and a deterministic color resolver function for curve names.
- [ ] (auto) Implement reactive multi-selection state:
  - `visibleCurveNames`: `Set<string>` or `string[]` of curves currently displayed on canvas (defaults to all room-associated curves, or all curves).
  - `activeCurveName`: `ref<string>` tracking the currently focused curve for editing points and fixture attachments.
- [ ] (auto) Ensure reactive synchronization when `brightnessCurves` prop changes (clean up deleted curves, auto-select if empty).

### 2. Multi-Curve Toggle Selector & Toolbar
**Files:** `web/src/components/CurveEditor.vue`

- [ ] (auto) Replace the single `<select>` dropdown in the header with a curve toggle bar:
  - Curve chips with color indicators, curve name, fixture count badge, visibility checkbox/eye toggle, and active focus badge.
  - Clicking a chip's visibility toggle shows/hides the curve on the canvas.
  - Clicking a chip selects that curve as the active editing target.
- [ ] (auto) Add quick toggle controls:
  - "All": Toggle all curves visible.
  - "None": Hide all curves except the active one.
  - "Room Fixtures": Filter/toggle curves assigned to lights in `roomLights`.
- [ ] (auto) Curve actions toolbar:
  - `+ New Curve`: Modal/prompt to create a curve with default control points.
  - Duplicate active curve button.
  - Delete active curve button (with confirmation if assigned to room lights).

### 3. Multi-Curve SVG Coordinate Canvas
**Files:** `web/src/components/CurveEditor.vue`, `web/src/utils/svg.ts`

- [ ] (auto) Generate dynamic SVG gradient definitions in `<defs>` for each visible curve color.
- [ ] (auto) Render paths for all visible curves:
  - Active curve: primary color, bold stroke (`stroke-width="3"`), shaded area gradient fill, interactive draggable control points.
  - Inactive visible curves: secondary opacity (`stroke-width="2"`, opacity ~0.7), clickable line and points with hover tooltip.
- [ ] (auto) Direct canvas interactions:
  - Clicking an inactive curve line or point on the canvas switches `activeCurveName` to that curve for immediate editing.
  - Dragging control points on the active curve updates `[x, y]` coordinates in real time and emits `update:previewRoomBrightness`.
  - Clicking empty canvas space adds a point to the active curve.
  - Double-clicking a point on the active curve deletes it (preserving minimum 2 points).
- [ ] (auto) Add vertical room brightness cursor line (if `previewRoomBrightness` or `roomBrightness` is active) indicating fixture output % across all visible curves.

### 4. Active Curve Details & Fine Tuning Panel
**Files:** `web/src/components/CurveEditor.vue`

- [ ] (auto) Render active curve summary header matching the curve's assigned theme color.
- [ ] (auto) Assigned room lights badge list with remove (`×`) and `+ Attach Room Light` menu (filtered to unassigned fixtures from `props.roomLights`).
- [ ] (auto) Points fine-tuning list with numeric step inputs for `Room %` and `Fixture %`.
- [ ] (auto) Support switching active curve directly from the panel or canvas.

### 5. Automated Unit & Integration Tests
**Files:** `web/src/components/CurveEditor.test.ts`

- [ ] (auto) Test multi-curve rendering: verifies multiple curve paths are rendered when multiple curves are visible.
- [ ] (auto) Test visibility toggle: verifies toggling curve visibility removes/adds its path from the SVG DOM.
- [ ] (auto) Test active curve switching: verifies clicking a curve chip or inactive canvas curve updates the active editing curve and control points.
- [ ] (auto) Test point manipulation on active curve: verifies dragging/adding points updates the active curve's points array.
- [ ] (auto) Test "All" / "None" quick toggle controls.
- [ ] (auto) Verify full web test suite (`npx vitest run`) and web build (`npm run build`) pass cleanly.
