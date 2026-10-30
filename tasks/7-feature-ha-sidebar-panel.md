# Task: ha sidebar panel

**Task:** #7
**Status:** pending
**Type:** feature
**Complexity:** large
**Mode:** auto
**Priority:** medium
**Category:** Features
**Summary:** Integrate web studio as Home Assistant sidebar panel with WebSocket config read/write endpoints
**Host:** all
**Created:** 2026-10-30
**Completed:** —

## Context

The Scheduled Scenes Studio has been developed as a standalone web application for rapid iteration. To provide a seamless, native user experience, this task integrates the studio directly into Home Assistant as a left navigation sidebar panel (`/scheduled-scenes`).

This integration requires:
1. **Integration WebSocket Endpoints:** Register Home Assistant WebSocket API handlers in Python to fetch existing configurations (`scheduled_scenes/config/get`) and save modifications (`scheduled_scenes/config/save`), automatically reloading the runtime coordinators.
2. **Sidebar Panel Registration:** Register a custom panel via Home Assistant's `frontend.async_register_built_in_panel` in `__init__.py`, serving the built frontend assets.
3. **Frontend HA Connection Adapter:** Enable the Vue app to detect when it is hosted inside Home Assistant, connecting to `window.hass` / Home Assistant WebSocket connection to read live entities and dispatch saves.
4. **HACS & Release Packaging:** Build scripts to bundle the compiled studio assets into `custom_components/scheduled_scenes/frontend/` so that users installing via HACS get the sidebar studio out-of-the-box.

## Affected hosts

- `all` — Custom component backend (`__init__.py`, new `websocket.py`), frontend studio (`web/`), and build scripts.

---

## Work items

### 1. Integration WebSocket API Endpoints
**Files:** `custom_components/scheduled_scenes/websocket.py`, `custom_components/scheduled_scenes/__init__.py`

- [ ] (auto) Create `websocket.py` registering WebSocket commands under the `scheduled_scenes/` namespace:
  - `ws_get_config`: Returns all configured programs, dim-to-warm curves, and brightness distribution curves.
  - `ws_save_config`: Validates incoming payload against `voluptuous` schemas, persists changes, and triggers `coordinator.async_refresh()` / reload.
- [ ] (auto) Register the WebSocket commands during `async_setup` in `custom_components/scheduled_scenes/__init__.py`.
- [ ] (auto) Add unit tests in `tests/test_websocket.py` for config retrieval and saving.

### 2. Frontend Panel Registration & Asset Serving
**Files:** `custom_components/scheduled_scenes/__init__.py`, `custom_components/scheduled_scenes/manifest.json`

- [ ] (auto) Configure static path serving in `__init__.py` mapping `/scheduled_scenes_panel/` to `custom_components/scheduled_scenes/frontend/dist/`.
- [ ] (auto) Register the sidebar panel:
  - Sidebar title: `"Scheduled Scenes"`
  - Icon: `"mdi:weather-sunset"` or `"mdi:theme-light-dark"`
  - Route: `"scheduled-scenes"`
  - Require admin: `True` (for configuration access).

### 3. Frontend Home Assistant Adapter
**Files:** `web/src/services/haBridge.ts`, `web/src/services/entityService.ts`, `web/src/App.vue`

- [ ] (auto) Create `haBridge.ts` detecting HA environment (`window.hass` or HA iframe postMessage bridge).
- [ ] (auto) Connect `entityService` to real `hass.states` when in HA mode, populating live `light.*` entities and area names.
- [ ] (auto) Replace or augment the YAML export bar with an **Apply to Home Assistant** button that calls `scheduled_scenes/config/save`.
- [ ] (auto) Add visual feedback (success toast, loading spinner, error banners) for save operations.

### 4. Build & Distribution Automation
**Files:** `web/vite.config.ts`, `pyproject.toml`, `hacs.json`

- [ ] (auto) Configure Vite `base` and output directory (`outDir: '../custom_components/scheduled_scenes/frontend/dist'`).
- [ ] (auto) Add build target `pnpm build:ha` in `web/package.json`.
- [ ] (auto) Ensure `.gitignore` and `hacs.json` properly handle the bundled frontend for distribution.

---

## Security considerations

- Configuration modification over WebSocket must enforce Home Assistant's admin authentication requirement (`@websocket_api.require_admin`).
- Saved configuration payloads must be strictly validated against voluptuous schemas before applying.

---

## Out-of-repo changes

None.

---

## Validation

- [ ] Unit tests for WebSocket API pass via `pytest tests/test_websocket.py`.
- [ ] Frontend builds cleanly into component directory.
- [ ] Integration loads in Home Assistant test environment and sidebar panel opens.

---

## Documentation updates

- [ ] Update `README.md` documenting the Home Assistant Sidebar Studio.
- [ ] Update `TODO.md` via `node ~/dev/dev-tools/scripts/todo-status.mjs --write`.

---

## Commit plan

| # | Scope | Files | Message |
|---|-------|-------|---------|
| 1 | backend | `custom_components/scheduled_scenes/websocket.py`, `tests/test_websocket.py` | `feat(api): add WebSocket endpoints for scheduled scenes configuration` |
| 2 | panel | `custom_components/scheduled_scenes/__init__.py`, `manifest.json` | `feat(panel): register Home Assistant sidebar panel and static assets` |
| 3 | web | `web/src/services/haBridge.ts`, `web/src/App.vue` | `feat(web): add live HA WebSocket adapter and direct save button` |
| 4 | wrap-up | `tasks/done/7-feature-ha-sidebar-panel-done.md`, `README.md`, `TODO.md` | `chore: mark task #7 as done` |

---

## Definition of done

- [ ] All work items checked off
- [ ] Security review passed (admin-only WS calls)
- [ ] Tests and build pass
- [ ] Documentation updated
