# Task: rename brightness distribution curves

**Task:** #16
**Status:** done
**Type:** feature
**Complexity:** small
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Allow renaming Room Brightness Distribution Curves with automatic reference updates
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

In Scheduled Scenes Studio, users configure fixture brightness distribution along 24-hour room brightness transitions using the **Room Brightness Distribution Curves** editor (`CurveEditor.vue`). Currently, users can create a new curve with `+ New Curve`, adjust control points, and attach or detach room fixtures, but there is no mechanism to rename an existing curve.

When configuring rooms, curve names often start with generic names (e.g. `curve_1` or `new_curve`), or room layouts evolve (e.g. an accent light is relocated, requiring a rename from `living_room_accent` to `cove_ambient_accent`). Without renaming support, users are forced to create a duplicate curve from scratch, manually re-enter all control points, re-assign fixtures, and delete the previous curve.

This task adds curve renaming functionality to `CurveEditor.vue` with:
1. **Inline & Accessible Rename UI:** A clean rename button (`✎ Rename`) next to the active curve title that switches to an inline text input with Save (`✓` / `Enter`) and Cancel (`✕` / `Escape`) controls.
2. **State & Dictionary Key Migration:** Safe key rename in `props.brightnessCurves` / `config.brightness_curves`, preserving curve points, assigned fixture entities (`curve.lights`), and updating the active selection (`selectedCurveName`) without resetting editor state.
3. **Validation & Duplicate Protection:** Validation preventing blank/whitespace names and rejecting collisions with existing curve names with clear error feedback.
4. **Seamless Multi-Curve & YAML Integration:** Compatibility with single-curve and multi-curve visibility modes (Task 15) and automatic serialization in `YamlViewer.vue` and Home Assistant configuration.

## Affected hosts

- `all` — Frontend studio files in `web/src/` (`components/CurveEditor.vue`, `components/CurveEditor.test.ts`).

---

## Work items

### 1. Rename UI & Inline Editing Controls
**Files:** `web/src/components/CurveEditor.vue`

- [x] (auto) Add rename state variables to `CurveEditor.vue`:
  - `isRenaming = ref(false)`
  - `renameInput = ref('')`
  - `renameError = ref<string | null>(null)`
  - `renameInputRef = ref<HTMLInputElement | null>(null)`
- [x] (auto) Render a `✎ Rename` action button adjacent to the active curve name badge in the details header.
- [x] (auto) Implement inline editing view when `isRenaming` is true:
  - Form input pre-populated with `activeCurve.name`.
  - Save button (`✓` or `Save`) triggering `confirmRename`.
  - Cancel button (`✕` or `Cancel`) triggering `cancelRename`.
  - Inline error badge/text displayed when `renameError` is non-null.
  - Keyboard handlers: `Enter` to confirm, `Escape` to cancel.
  - Auto-focus and text select when entering rename mode via `nextTick()`.

### 2. State & Dictionary Key Synchronization Logic
**Files:** `web/src/components/CurveEditor.vue`

- [x] (auto) Implement `startRename()`:
  - Set `renameInput.value = activeCurve.value.name`.
  - Clear `renameError.value`.
  - Set `isRenaming.value = true`.
- [x] (auto) Implement `confirmRename()`:
  - Trim `trimmedName = renameInput.value.trim()`.
  - Validation checks:
    - If empty, set `renameError.value = 'Curve name cannot be empty.'`.
    - If identical to current name (`trimmedName === activeCurve.value.name`), exit rename mode with no changes.
    - If `props.brightnessCurves[trimmedName]` exists, set `renameError.value = "A curve named '" + trimmedName + "' already exists."`.
  - Key migration in `props.brightnessCurves`:
    - Migrate curve under new key: `props.brightnessCurves[trimmedName] = activeCurve.value`.
    - Update `activeCurve.value.name = trimmedName`.
    - Delete old key: `delete props.brightnessCurves[oldName]`.
    - Update reactive selection: `selectedCurveName.value = trimmedName`.
    - If multi-curve selection (`visibleCurveNames`) exists, migrate `oldName` to `trimmedName`.
    - Exit rename mode: `isRenaming.value = false; renameError.value = null`.
- [x] (auto) Implement `cancelRename()`:
  - Reset `isRenaming.value = false` and `renameError.value = null`.

### 3. Fixture Association, YAML Export & Parity Verification
**Files:** `web/src/components/CurveEditor.vue`, `web/src/components/YamlViewer.vue`

- [x] (auto) Verify assigned light fixtures in `activeCurve.lights` remain intact through the rename.
- [x] (auto) Verify `ScrubSimulator.vue` continues calculating fixture output accurately after renaming a curve assigned to room lights.
- [x] (auto) Verify `YamlViewer.vue` immediately exports the updated curve key under `scheduled_scenes.brightness_curves.<newName>`.

### 4. Automated Tests
**Files:** `web/src/components/CurveEditor.test.ts`

- [x] (auto) Test that `✎ Rename` button renders next to the active curve name.
- [x] (auto) Test entering rename mode renders input pre-filled with the active curve's name.
- [x] (auto) Test successful rename:
  - Renaming updates dictionary key in `brightnessCurves`.
  - Updates `activeCurve.name`.
  - Preserves control points and fixture lights array.
  - Updates selector dropdown value.
- [x] (auto) Test duplicate name rejection: entering an existing curve name displays error and does not mutate curves.
- [x] (auto) Test empty name rejection: entering whitespace shows error and prevents rename.
- [x] (auto) Test cancel / Escape restores original display without mutating curves.
- [x] (auto) Verify full web test suite passes (`npx vitest run`) and build passes (`npm run build --prefix web`).

---

## Security considerations

None — client-side UI and state transformation; no secrets, network permissions, or privileged APIs involved.

---

## Out-of-repo changes

None.

---

## Validation

- [x] `npx vitest run` in `web/` passes all tests.
- [x] `npm run build` in `web/` completes cleanly.
- [x] `node ~/dev/dev-tools/scripts/todo-status.mjs --check` passes without drift.

---

## Documentation updates

- [x] Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write` to sync `TODO.md` / `NEEDS-FROM-YOU.md`.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | web | `web/src/components/CurveEditor.vue`, `web/src/components/CurveEditor.test.ts` | `feat(web): allow renaming room brightness distribution curves` |
| N | wrap-up | `tasks/done/16-feature-rename-brightness-distribution-curves-done.md`, `TODO.md` | `chore: mark task #16 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] Security review passed
- [x] Validation passes (`npx vitest run` and `npm run build`)
- [x] Documentation updated
