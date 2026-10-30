# Task: studio room light manager

**Task:** #6
**Status:** done
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Interactive room fixture selector with area search, custom entity entry, and reactive curve sync
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

Currently in `App.vue`, room lights are displayed as static, read-only badges. Adding a new room hardcodes a single light, and there is no UI mechanism to add or remove fixtures from a room program within the studio.

To make the studio a full-featured configurator, this task introduces an interactive Room Light Manager component (`RoomLightManager.vue`):
1. **Interactive Light Management:** Add lights from an area-grouped dropdown, search by friendly name / entity ID, add custom entity IDs, and remove fixtures with a single click (`×`).
2. **Area-Aware Suggestions:** When configuring a room, automatically highlight or suggest lights matching the room's name or area.
3. **Reactive Multi-Component Sync:** Adding or removing a light immediately reflects across:
   - The live **Scrub Simulator** (fixture cards appear/disappear instantly).
   - The **Curve Editor** (fixtures available for Dim-to-Warm & Brightness distribution curves).
   - The **YAML Sync** tab (emits updated `lights:` list).

## Affected hosts

- `all` — Frontend studio files in `web/src/` (`components/RoomLightManager.vue`, `App.vue`, `components/CurveEditor.vue`).

---

## Work items

### 1. RoomLightManager Component
**Files:** `web/src/components/RoomLightManager.vue`

- [x] (auto) Create `RoomLightManager.vue` accepting `modelValue: string[]` (active room light IDs) and emitting `update:modelValue`.
- [x] (auto) Render assigned light chips with:
  - Entity friendly name (resolved from entity service) and entity ID.
  - Quick dismiss button (`×`) to remove fixture from room.
- [x] (auto) Implement `+ Add Light` popover / searchable dropdown:
  - Search input filtering by friendly name or entity ID.
  - Group available lights by Home Assistant Area (e.g. *Living Room*, *Kitchen*, *Bedroom*).
  - Hide or disable already-assigned lights.
  - "Custom Entity ID" input to manually attach any entity ID (e.g. `light.patio_spots`).
- [x] (auto) Add confirmation when removing a fixture that is actively mapped to a curve.

### 2. Integration into Studio Workspace
**Files:** `web/src/App.vue`

- [x] (auto) Replace static Target Lights chip section in `App.vue` with `<RoomLightManager v-model="currentProgram.lights" />`.
- [x] (auto) Update `addNewProgram` flow in `App.vue` to allow selecting initial lights or starting with an empty light list.
- [x] (auto) Ensure room name changes or area selection updates suggested lights.

### 3. Reactive Sync with Simulator & Curve Editors
**Files:** `web/src/components/ScrubSimulator.vue`, `web/src/components/CurveEditor.vue`, `web/src/components/YamlViewer.vue`

- [x] (auto) Verify `ScrubSimulator` immediately mounts/unmounts fixture cards when lights are added/removed.
- [x] (auto) Update `CurveEditor` fixture picker dropdown so newly added room fixtures can be assigned to curves, and removed fixtures are unlinked or flagged.
- [x] (auto) Verify `YamlViewer` immediately reflects changes in exported YAML.

---

## Security considerations

None — Client-side studio component.

---

## Out-of-repo changes

None.

---

## Validation

- [x] Add fixture from dropdown -> appears in chips, simulator, and YAML output.
- [x] Remove fixture -> chip disappears, simulator card disappears, and YAML updates.
- [x] Add custom entity ID -> correctly handled and displayed.
- [x] `pnpm --dir web build` compiles cleanly.

---

## Documentation updates

- [x] Update `TODO.md` via `node ~/dev/dev-tools/scripts/todo-status.mjs --write`.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | web | `web/src/components/RoomLightManager.vue`, `web/src/App.vue` | `feat(web): add interactive room light manager with area search and custom entity entry` |
| 2 | wrap-up | `tasks/done/6-feature-studio-room-light-manager-done.md`, `TODO.md` | `chore: mark task #6 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] UI interaction verified in browser
- [x] Type checks and build pass
