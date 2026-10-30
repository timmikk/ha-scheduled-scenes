# Task: studio ha mock entities

**Task:** #5
**Status:** done
**Type:** feature
**Complexity:** small
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Model mock lights with Home Assistant entity schema, areas, and an entity provider service
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

Currently, `web/src/mock/data.ts` and `web/src/types.ts` define a simplified `MockLight` containing only `entity_id`, `name`, and min/max Kelvin. In Home Assistant, entities have richer metadata: `entity_id`, `friendly_name`, `area_id`, `area_name`, `state`, and `supported_color_modes` (e.g. `color_temp`, `brightness`, `hs`).

To prepare the studio for smooth migration to a Home Assistant sidebar panel and enable area-based room fixture picking, this task:
1. Expands the entity model to mirror Home Assistant's entity and area registries.
2. Expands the mock dataset with realistic fixtures across multiple areas (Living Room, Kitchen, Bedroom, Office).
3. Introduces a pluggable entity provider service abstraction (`entityService.ts`) so UI components interact with a unified interface whether powered by local mock data or live `hass.states`.

## Affected hosts

- `all` — Frontend studio files in `web/src/` (`types.ts`, `mock/data.ts`, `services/entityService.ts`, and consuming components).

---

## Work items

### 1. Home Assistant Entity & Area Types
**Files:** `web/src/types.ts`

- [x] (auto) Define `HAArea` interface with `area_id: string` and `name: string`.
- [x] (auto) Define `HALightEntity` interface with:
  - `entity_id: string`
  - `name: string`
  - `area_id?: string`
  - `area_name?: string`
  - `state?: 'on' | 'off'`
  - `supported_color_modes?: string[]`
  - `min_color_temp_kelvin?: number`
  - `max_color_temp_kelvin?: number`
- [x] (auto) Maintain backwards compatibility with `MockLight` type alias.

### 2. Realistic HA Mock Dataset
**Files:** `web/src/mock/data.ts`

- [x] (auto) Define `MOCK_AREAS: HAArea[]` including Living Room, Kitchen, Bedroom, Office, and Hallway.
- [x] (auto) Expand `MOCK_LIGHTS: HALightEntity[]` with realistic fixtures mapped to areas:
  - Living Room: Cove Strip (tunable white), Ceiling Downlights (tunable white), Reading Floor Lamp (tunable white), Accent Spot (dimmable only).
  - Kitchen: Counter LED Strip (tunable white), Main Spotlights (tunable white), Island Pendants (tunable white).
  - Bedroom: Bedside Pendants (dim-to-warm), Main Ceiling (tunable white).
  - Office: Desk Task Light (tunable white), Wall Washers (tunable white).

### 3. Entity Provider Abstraction
**Files:** `web/src/services/entityService.ts`, `web/src/composables/useEntities.ts`

- [x] (auto) Create `entityService.ts` exposing:
  - `getAllLights(): HALightEntity[]`
  - `getLight(entityId: string): HALightEntity | undefined`
  - `getAllAreas(): HAArea[]`
  - `getLightsByArea(areaId: string): HALightEntity[]`
  - `searchLights(query: string): HALightEntity[]`
- [x] (auto) Design the provider with a pluggable source so it can switch from mock data to `hass.states` when running inside Home Assistant.
- [x] (auto) Update `ScrubSimulator.vue` and `App.vue` to use the entity provider.

---

## Security considerations

None — Client-side mock data and entity type definitions in development studio.

---

## Out-of-repo changes

None.

---

## Validation

- [x] `pnpm --dir web build` compiles cleanly without TypeScript errors.
- [x] Dev server renders all mock entities with area associations.

---

## Documentation updates

- [x] Update `TODO.md` via `node ~/dev/dev-tools/scripts/todo-status.mjs --write`.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | web | `web/src/types.ts`, `web/src/mock/data.ts`, `web/src/services/entityService.ts` | `feat(web): add HA entity schema, area metadata, and entity provider service` |
| 2 | wrap-up | `tasks/done/5-feature-studio-ha-mock-entities-done.md`, `TODO.md` | `chore: mark task #5 as done` |

---

## Definition of done

- [x] All work items checked off
- [x] Type checks and production build succeed
- [x] Documentation updated
