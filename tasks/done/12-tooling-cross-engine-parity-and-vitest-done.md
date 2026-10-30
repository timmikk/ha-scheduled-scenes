# Task: cross engine parity and vitest

**Task:** #12
**Status:** done
**Type:** tooling
**Complexity:** medium
**Mode:** auto
**Priority:** high
**Category:** Quality & Tooling
**Summary:** Setup Vitest and create shared cross-engine calculation parity test suite
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

The Home Assistant Python backend (`custom_components/scheduled_scenes/logic.py`) and the Studio frontend (`web/src/utils/interpolator.ts`) independently implement identical scheduling and curve projection algorithms:
- Time-of-day parsing and midnight wrap-around resolution.
- Piecewise linear room brightness curves (`evaluateBrightnessCurve`).
- Dim-to-warm Kelvin curves (`evaluateDimToWarm`).
- Per-fixture offset and scalar interpolation rounding.

Currently, `web/` has zero automated tests, and there are no parity fixtures comparing the two implementations. If rounding conventions, boundary clamping, or interpolation edge cases diverge, users will experience a discrepancy between the Studio visual simulator and Home Assistant's real light states.

This task sets up Vitest in `web/` and introduces a language-agnostic test fixture dataset executed by both Pytest and Vitest.

## Affected hosts

- `all` — `web/package.json`, `web/src/utils/`, `tests/fixtures/`, `tests/test_parity.py`, and `.forgejo/workflows/ci.yml`.

---

## Work items

### 1. Vitest Setup in Web Studio
**Files:** `web/package.json`, `web/vite.config.ts`, `web/tsconfig.json`

- [x] (auto) Install `vitest` in `web/package.json` devDependencies.
- [x] (auto) Add test scripts: `"test": "vitest"`, `"test:run": "vitest run --coverage"`.
- [x] (auto) Create unit tests for utility functions in `web/src/utils/`:
  - `interpolator.test.ts`: Test `timeToMinutes`, `minutesToTime`, `interpolateScalar`, `evaluateBrightnessCurve`, `evaluateDimToWarm`.
  - `color.test.ts`: Test Kelvin to RGB / hex conversions.
  - `svg.test.ts`: Test coordinate mapping utilities.

### 2. Language-Agnostic Parity Fixture Suite
**Files:** `tests/fixtures/parity_cases.json`, `tests/test_parity.py`, `web/src/utils/parity.test.ts`

- [x] (auto) Create `tests/fixtures/parity_cases.json` specifying:
  - Standard curve points and schedules (including midnight crossings).
  - Target evaluation timestamps throughout 24 hours.
  - Expected outputs `(brightness, temp_kelvin)` for various light IDs.
- [x] (auto) Ingest `tests/fixtures/parity_cases.json` in `tests/test_parity.py` using `pytest.mark.parametrize`.
- [x] (auto) Ingest `tests/fixtures/parity_cases.json` in `web/src/utils/parity.test.ts` using Vitest `test.each`.
- [x] (auto) Verify that Python and TypeScript implementations yield identical outputs across all test cases.

### 3. CI Pipeline Integration
**Files:** `.forgejo/workflows/ci.yml`

- [x] (auto) Add `pnpm --dir web test:run` to the CI workflow so that calculation regressions in either backend or frontend break the build.
