# Changelog

All notable changes to this project will be documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-28

### Added
- Room brightness distribution curves (`brightness_curves`) mapping overall room brightness to fixture brightness with piecewise linear interpolation (task #2).
- Smooth start brightness estimation via mathematical curve inversion, preventing sudden jumps or wrong-direction stepping when adjusting brightness from physical remotes or wall buttons (task #2).
- Manual override tracking with suspension of periodic automated schedule transitions while manual brightness is active (task #2).
- Domain services `scheduled_scenes.adjust_brightness`, `scheduled_scenes.step_brightness`, and `scheduled_scenes.resume_schedule`, plus per-program legacy service aliases (task #2).
- Diagnostic sensor attributes `manual_override` and `manual_brightness` on `sensor.<name>_schedule_phase` (task #2).
- Dim-to-warm curves support for physical light models with automatic brightness-to-Kelvin derivation (task #1).
- Piecewise linear curve interpolation engine with boundary clamping in `logic.py` (task #1).
- Shared entity curve mapping: multiple entities can share a single physical light model curve (task #1).
- Dual point format support: verbose dictionary mappings (`[{brightness: 1, temp: 2200}, ...]`) and compact coordinate pairs (`[[1, 2200], [100, 4000]]`).
- Support for schedule steps omitting `temp` or using `dim_to_warm` / `dimm_to_warm` aliases while preserving backwards-compatibility with explicit temperature checkpoints (task #1).
- Two-tier curve configuration: global top-level curves under `scheduled_scenes.curves` or scoped curves per program/room, plus UI config flow / options flow support.

## [0.1.1] - 2026-10-27

### Fixed
- Fix `homeassistant` minimum version in `hacs.json`: remove invalid `>=` prefix that broke HACS `AwesomeVersion` validation, and lower required version from `2026.6.0` to `2026.5.0` to support current fleet HA runtime (`2026.5.4`).

## [0.1.0] - 2026-10-27

### Added
- Feature parity implementation of scheduled circadian scenes matching legacy pyscript app.
- Pure interpolation logic engine (`logic.py`) with continuous linear curve calculation and midnight wrapping.
- Two-tier configuration: declarative YAML matching pyscript schema 1:1, and Home Assistant Config Flow / Options Flow with multiline schedule validator.
- Runtime coordinator with periodic interval timers, entity state triggers, and duration disable timer.
- Platforms: `switch.schedule_<name>` and `sensor.<name>_schedule_phase`.
- Services: `scheduled_scenes.turn_on`, `turn_off`, `enable`, `disable`, `reload`, plus legacy alias services.

## [0.0.1] - 2026-10-27

- Initial scaffold via infra task #200 (`scripts/setup-ha-component-repo.sh`).
  Empty `async_setup` shell; not yet functional.
