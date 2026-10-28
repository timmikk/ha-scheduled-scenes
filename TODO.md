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

