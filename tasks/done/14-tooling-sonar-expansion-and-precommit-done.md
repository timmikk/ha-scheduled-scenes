# Task: sonar expansion and precommit

**Task:** #14
**Status:** done
**Type:** tooling
**Complexity:** medium
**Mode:** auto
**Priority:** medium
**Category:** Quality & Tooling
**Summary:** Expand SonarQube scope to PRs/Studio and configure local pre-commit gates
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

To establish long-term engineering rigor and prevent regressions from reaching remote branches:
1. SonarQube analysis currently only triggers on `push` to `main`, bypassing pull request validation and preventing automated feedback during code review.
2. In `sonar-project.properties`, `custom_components/scheduled_scenes/__init__.py` is excluded from coverage tracking, and `web/` is excluded entirely from Sonar source scanning.
3. Developers currently have no automated pre-commit hook setup to format Python code or check TypeScript types locally prior to pushing.
4. Python coordinator branch coverage currently sits at 83% with 34 missed branches, primarily around edge-case error recovery (e.g. unreachable lights, unexpected HA events, and options reload errors).

This task enables PR-level SonarQube analysis, broadens analysis to include the Studio frontend, sets up standardized pre-commit hooks, and closes backend coordinator branch coverage gaps.

## Affected hosts

- `all` — `.pre-commit-config.yaml`, `sonar-project.properties`, `.forgejo/workflows/ci.yml`, and `tests/test_coordinator.py`.

---

## Work items

### 1. Pre-Commit Hook Configuration
**Files:** `.pre-commit-config.yaml`

- [x] (auto) Create `.pre-commit-config.yaml` with hooks:
  - `ruff` (linter and formatter).
  - `mypy` (type-checker).
  - `vue-tsc` (Studio TypeScript validation).
  - Shared todo consistency check (`node /home/timo/dev/dev-tools/scripts/todo-status.mjs --check`).
- [x] (auto) Document installation (`pre-commit install`) in `README.md`.

### 2. SonarQube Scope and Pull Request Integration
**Files:** `sonar-project.properties`, `.forgejo/workflows/ci.yml`

- [x] (auto) Update `sonar-project.properties`:
  - Include `web/src` in `sonar.sources`.
  - Remove `custom_components/scheduled_scenes/__init__.py` from `sonar.coverage.exclusions`.
- [x] (auto) Update `.forgejo/workflows/ci.yml` to trigger SonarQube analysis on pull requests against `main` in addition to push events.

### 3. Backend Error Branch Coverage Expansion
**Files:** `tests/test_coordinator.py`

- [x] (auto) Add unit tests for coordinator edge cases:
  - Entity registry change where a tracked light is deleted or renamed.
  - Service call `light.turn_on` raising Home Assistant exceptions.
  - Recovery behavior when unavailable lights transition back to available.
- [x] (auto) Verify total coordinator statement coverage exceeds 85% and branch coverage exceeds 85%.
