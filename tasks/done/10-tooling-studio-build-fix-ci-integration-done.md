# Task: studio build fix ci integration

**Task:** #10
**Status:** done
**Type:** tooling
**Complexity:** small
**Mode:** auto
**Priority:** high
**Category:** Quality & Tooling
**Summary:** Fix Studio TypeScript build error and integrate web build into CI pipeline
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

The Scheduled Scenes Studio web application under `web/` is currently not verified by any continuous integration workflow. Furthermore, running `pnpm run build` in `web/` immediately fails with `TS1127: Invalid character` and `TS1005: ',' expected` at line 3 of `web/src/mock/data.ts` due to an unescaped literal `[\n`.

Because the CI workflow (`.forgejo/workflows/ci.yml`) only tests the Python backend, frontend compilation breaks go unnoticed. This task resolves the build blocker and establishes baseline CI verification for the Studio frontend.

## Affected hosts

- `all` — `web/src/mock/data.ts`, `.forgejo/workflows/ci.yml`, and `web/package.json`.

---

## Work items

### 1. Fix TypeScript Syntax Error in Mock Data
**Files:** `web/src/mock/data.ts`

- [x] (auto) Fix array initialization on line 3 of `web/src/mock/data.ts` by replacing the malformed literal `[\n` with clean multiline array syntax.
- [x] (auto) Run `pnpm --dir web run build` locally to verify that `vue-tsc --noEmit && vite build` completes with exit code 0.

### 2. CI Workflow Integration for Studio
**Files:** `.forgejo/workflows/ci.yml`

- [x] (auto) Add a dedicated `web-build` job to `.forgejo/workflows/ci.yml`:
  - Set up Node.js (v20) and pnpm (v9) with action cache keyed on `web/pnpm-lock.yaml`.
  - Execute `pnpm --dir web install --frozen-lockfile`.
  - Execute `pnpm --dir web run build` (type-checking + Vite production bundle).
- [x] (auto) Ensure the job runs on both `push: branches: [main]` and `pull_request: branches: [main]`.
