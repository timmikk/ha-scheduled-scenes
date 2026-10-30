# Task: timeline and brightness curve yaml copy import

**Task:** #17
**Status:** done
**Type:** feature
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Allow copying and importing YAML in Circadian Timeline and Brightness Distribution curve views for easy cross-room and configuration reuse
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

In Scheduled Scenes Studio, users configure circadian schedule timelines (`CircadianTimeline.vue`) and room brightness distribution curves (`CurveEditor.vue`). Currently, sharing a tuned circadian timeline schedule or brightness distribution curve across different rooms requires either manually re-creating all checkpoints/control points by hand in each room or editing the raw global configuration YAML at the bottom of the page in `YamlViewer.vue`.

Users need the ability to quickly copy and import curves directly within the visual curve editors:
1. **24-Hour Circadian Schedule Timeline:** Export the active room's schedule checkpoints to clipboard as clean YAML, and import/paste schedule YAML into any room with schema validation and immediate curve visualization.
2. **Room Brightness Distribution Curves:** Export active curve control points/definitions to clipboard as clean YAML, and import/paste curve YAML points to apply to existing or newly created curves.

This feature enables seamless workflow between rooms (e.g. tuning a 24-hour schedule in the Living Room, copying its YAML, and importing it into the Bedroom or Office) as well as sharing curve presets across Home Assistant installations.

## Affected hosts

- `all` — Frontend studio files in `web/src/` (`components/CircadianTimeline.vue`, `components/CurveEditor.vue`, `utils/curveYaml.ts`, unit tests, and `App.vue`).

---

## Work items

### 1. Curve & Schedule YAML Utilities
**Files:** `web/src/utils/curveYaml.ts`, `web/src/utils/curveYaml.test.ts`

- [x] (auto) Implement `serializeScheduleYaml(steps: ScheduleStep[]): string` producing standard Home Assistant `schedule:` list format.
- [x] (auto) Implement `parseScheduleYaml(yamlStr: string): { success: boolean; data?: ScheduleStep[]; error?: string }`:
  - Support input with `schedule:` key prefix, bare YAML list (`- time: ...`), or JSON array.
  - Validate time format (`HH:MM`), brightness range (`0-100`), and optional Kelvin temperature.
  - Automatically assign IDs to imported steps if missing.
- [x] (auto) Implement `serializeCurvePointsYaml(points: [number, number][], name?: string): string` for brightness distribution curves.
- [x] (auto) Implement `parseCurvePointsYaml(yamlStr: string): { success: boolean; points?: [number, number][]; name?: string; error?: string }`:
  - Support bare 2D point arrays (`[[0, 0], [50, 100]]`), `points:` YAML mapping, or complete curve definitions.
  - Validate points are number pairs in 0–100 range and monotonically increasing on X axis.
- [x] (auto) Add unit test coverage in `web/src/utils/curveYaml.test.ts` covering valid inputs, edge cases, malformed YAML, and boundary validation errors.

### 2. Circadian Timeline Copy & Import Features
**Files:** `web/src/components/CircadianTimeline.vue`, `web/src/components/CircadianTimeline.test.ts`

- [x] (auto) Add "📋 Copy YAML" button in CircadianTimeline header:
  - Serializes `props.steps` via `serializeScheduleYaml`.
  - Writes to clipboard via `navigator.clipboard.writeText` (with fallback).
  - Shows temporary feedback (e.g. "✓ Copied!").
- [x] (auto) Add "📥 Import YAML" button in CircadianTimeline header opening an import modal:
  - Textarea for pasting YAML snippet with placeholder guide.
  - Real-time syntax & schema validation with descriptive error alert on failure.
  - Live summary of parsed steps (checkpoint count, time span).
  - "Apply to Room" button: updates timeline checkpoints, emits `update:steps`, and closes modal.
  - Modal dismissal via backdrop click, close button, or Escape key.
- [x] (auto) Add unit tests verifying copy trigger and import modal parsing/validation/apply flow.

### 3. Room Brightness Curve Copy & Import Features
**Files:** `web/src/components/CurveEditor.vue`, `web/src/components/CurveEditor.test.ts`

- [x] (auto) Add "📋 Copy YAML" button in CurveEditor toolbar:
  - Serializes active curve's points/definition via `serializeCurvePointsYaml`.
  - Writes to clipboard with temporary feedback ("✓ Copied!").
- [x] (auto) Add "📥 Import YAML" button in CurveEditor toolbar opening an import modal:
  - Textarea for pasting YAML points / curve snippet.
  - Validation for coordinate pairs and monotonic ordering.
  - Choice to apply/replace points on active curve or import as a new named curve.
  - Updates reactive curve state and emits changes.
- [x] (auto) Add unit tests verifying curve copy and import modal behavior.

### 4. Integration Verification & Build
**Files:** `web/src/`

- [x] (auto) Verify cross-room workflow in Studio: copy schedule YAML from one room, switch room tab, and import cleanly.
- [x] (auto) Run `pnpm --dir web run test:run` to verify all Vitest unit tests pass.
- [x] (auto) Run `pnpm --dir web run build` to verify TypeScript type-checking and production bundle compilation.

---

## Security considerations

None — client-side UI and state transformation; no secrets, network permissions, or privileged APIs involved.

---

## Out-of-repo changes

None.

---

## Validation

- [x] `pnpm --dir web run test:run` passes all tests cleanly (9 test files, 63 tests).
- [x] `pnpm --dir web run build` completes cleanly without errors or warnings.
- [x] `node ~/dev/dev-tools/scripts/todo-status.mjs --check` passes without drift.

---

## Documentation updates

- [x] Run `node ~/dev/dev-tools/scripts/todo-status.mjs --write` to sync `TODO.md` / `NEEDS-FROM-YOU.md`.

---

## Definition of done

- [x] All work items checked off
- [x] Security review passed
- [x] Validation passes (`vitest` and `build`)
- [x] Documentation updated
