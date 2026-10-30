# Task: studio ui testing

**Task:** #13
**Status:** done
**Type:** tooling
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Quality & Tooling
**Summary:** Automate Studio UI testing with Vue component tests and Playwright headless smoke tests
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

The Scheduled Scenes Studio (`web/`) is an interactive visual editor featuring SVG curve canvases (`CurveEditor.vue`), 24-hour circadian timeline bars (`CircadianTimeline.vue`), real-time simulation scrubbers (`ScrubSimulator.vue`), and synchronized YAML editors (`YamlViewer.vue`).

Currently, there is no automated verification of UI rendering, user interaction, or browser stability. Manual testing is required to verify that dragging a curve point updates the chart and YAML correctly without throwing JavaScript runtime exceptions.

This task automates UI testing across two complementary levels:
1. **Component Interaction Tests**: Using `@vue/test-utils` and `happy-dom` for fast, lightweight testing of component events, sliders, and buttons without launching a browser.
2. **Headless Browser Smoke Tests**: Using `@playwright/test` running against Vite's dev server to verify critical end-to-end user flows (loading rooms, scrubbing time, dragging SVG points, and exporting YAML) with zero console errors.

## Affected hosts

- `all` — `web/package.json`, `web/playwright.config.ts`, `web/src/components/`, `web/e2e/`, and `.forgejo/workflows/ci.yml`.

---

## Work items

### 1. Component Interaction Tests with `@vue/test-utils`
**Files:** `web/package.json`, `web/src/components/*.test.ts`

- [x] (auto) Install `@vue/test-utils` and `happy-dom` in `web/package.json`.
- [x] (auto) Write component tests for `ScrubSimulator.vue`:
  - Verify slider scrub updates the current minute and computed light outputs.
  - Verify live mode toggle triggers state changes.
- [x] (auto) Write component tests for `CurveEditor.vue`:
  - Verify control points render as SVG circle elements.
  - Verify clicking to add/delete a point emits updated curve points.
- [x] (auto) Write component tests for `YamlViewer.vue`:
  - Verify syntax highlighting renders without crash.
  - Verify copy-to-clipboard button interaction.

### 2. Playwright Headless Browser Smoke Suite
**Files:** `web/playwright.config.ts`, `web/e2e/studio.spec.ts`

- [x] (auto) Add `@playwright/test` to `web/package.json`.
- [x] (auto) Configure `web/playwright.config.ts` to automatically spawn `pnpm run dev` at `http://localhost:5173` with headless Chromium.
- [x] (auto) Write end-to-end smoke test spec `web/e2e/studio.spec.ts`:
  - Assert the studio page loads cleanly with zero browser console errors.
  - Assert default mock areas (`Living Room`, `Kitchen`) and lights load from mock data.
  - Assert moving the timeline slider alters live fixture brightness/Kelvin display badges.
  - Assert switching between Room Tabs, Dim-to-Warm tab, and YAML tab maintains state.

### 3. CI Pipeline Integration
**Files:** `.forgejo/workflows/ci.yml`

- [x] (auto) Add Playwright test execution step to the CI workflow (`pnpm --dir web run test:e2e`).
- [x] (auto) Cache Playwright browser binaries to keep CI runtime under 30 seconds.
