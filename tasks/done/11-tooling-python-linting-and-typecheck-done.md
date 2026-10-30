# Task: python linting and typecheck

**Task:** #11
**Status:** done
**Type:** tooling
**Complexity:** medium
**Mode:** auto
**Priority:** high
**Category:** Quality & Tooling
**Summary:** Configure Ruff lint/format and Mypy strict type checking in CI and pyproject.toml
**Host:** all
**Created:** 2026-10-30
**Completed:** 2026-10-30

## Context

Static code analysis and typing in the Python backend are currently unmonitored:
1. `ruff` is installed in the CI container during the `hassfest` step but is never executed against the repository files.
2. `mypy` is not run in CI or configured in `pyproject.toml`. Running Mypy currently reveals 5 type errors in `custom_components/scheduled_scenes/coordinator.py` and `__init__.py`.
3. Code formatting is not enforced, leaving potential style drifts between contributions.

This task resolves existing type inconsistencies and puts strict linting, formatting, and typing gates into CI and `pyproject.toml`.

## Affected hosts

- `all` — `pyproject.toml`, `requirements_test.txt`, `custom_components/scheduled_scenes/`, and `.forgejo/workflows/ci.yml`.

---

## Work items

### 1. Resolve Existing Mypy Type Errors
**Files:** `custom_components/scheduled_scenes/coordinator.py`, `custom_components/scheduled_scenes/__init__.py`

- [x] (auto) Fix event listener signature in `coordinator.py` line 297 for `async_track_state_change_event` callback parameter typing.
- [x] (auto) Fix `int | None` conversion in `coordinator.py` line 483 with proper fallback or None-check guard.
- [x] (auto) Fix dictionary assignment type annotations in `custom_components/scheduled_scenes/__init__.py` lines 145-149.
- [x] (auto) Verify `mypy custom_components` passes cleanly with 0 errors.

### 2. Configure Ruff and Mypy in `pyproject.toml`
**Files:** `pyproject.toml`, `requirements_test.txt`

- [x] (auto) Add `ruff` and `mypy` to `requirements_test.txt` (or dev dependencies).
- [x] (auto) Configure `[tool.ruff]` in `pyproject.toml` with target version Python 3.12, enabling standard rules (`E`, `F`, `W`, `I`, `UP`).
- [x] (auto) Configure `[tool.mypy]` with `ignore_missing_imports = true` and `check_untyped_defs = true`.

### 3. Integrate Lint and Type Checks into CI
**Files:** `.forgejo/workflows/ci.yml`

- [x] (auto) Add a `lint` job running `ruff check custom_components tests` and `ruff format --check custom_components tests`.
- [x] (auto) Add `mypy custom_components` step to verify type safety on pull requests and pushes to `main`.
