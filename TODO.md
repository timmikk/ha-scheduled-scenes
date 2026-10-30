# ha-scheduled-scenes TODO

GENERATED from `tasks/*.md` frontmatter by the shared `todo-status.mjs` — **do not
edit by hand**; run `make todo` (`--write`). `make todo-check` (pre-commit / CI)
regenerates and diffs, failing on any drift or a missing/invalid field.

Each active task file (`tasks/<N>-*.md`, excluding `tasks/done/`) supplies the
dashboard fields: **Priority** (urgent/high/medium/low), **Category** (the
section), **Summary** (the blurb after the em-dash), and **Host**. **Size** is
derived from **Complexity** (small→S, medium→M, large→L); **Status** and **Mode**
are read straight from the file. Entries are grouped by Category (fixed order from
`.todo-config.json`) and sorted by priority (urgent→low), then task number. A
`deferred` task shows its **Revisit** date; completed tasks leave this board for
`tasks/done/`.

---

## Features

- [ ] **#18 dynamic sun timeline curve points** — Support dynamic timeline curve
  points fixed to sun events and elevation angles with yearly variation
  visualization, seasonal simulator scrubbing, and deterministic overlap
  handling `tasks/18-feature-dynamic-sun-timeline-curve-points.md`
  **Status:** pending | **Priority:** high | **Size:** L | **Mode:** auto | **Host:** all

- [ ] **#7 ha sidebar panel** — Integrate web studio as Home Assistant sidebar
  panel with WebSocket config read/write endpoints
  `tasks/7-feature-ha-sidebar-panel.md`
  **Status:** pending | **Priority:** medium | **Size:** L | **Mode:** auto | **Host:** all

- [ ] **#15 multi curve brightness editor** — Allow viewing and editing multiple
  room brightness distribution curves simultaneously with toggle visibility
  selector `tasks/15-feature-multi-curve-brightness-editor.md`
  **Status:** pending | **Priority:** medium | **Size:** M | **Mode:** auto | **Host:** all
