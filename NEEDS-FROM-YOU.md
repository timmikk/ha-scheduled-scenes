# Needs from you

GENERATED from `tasks/*.md` `**Needs from you:**` — do not edit by hand; run `make todo`.

This board is the always-current "needs you" queue: the outstanding manual steps
(web UI clicks, hardware access, secret entry, prod verification) across every
**active** task, lifted verbatim from each task file's `**Needs from you:**`
block. It is regenerated from the task files by the shared `todo-status.mjs`
(`make todo`) and gated by `make todo-check` / pre-commit, so it never drifts
and survives chat scroll-off. The task file stays the source of truth; this is
the generated projection. Done tasks drop off automatically.

Entries are ordered by status (pending-user / blocked first, then in-progress,
then deferred) and then by task number. "Passive confirmations" — blocks that
open with *nothing actionable* — are listed separately at the bottom; they need
no action yet, only an eventual observation before the task flips to `done`.

*No outstanding actions — nothing is waiting on you right now.*
