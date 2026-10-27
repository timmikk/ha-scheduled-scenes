# Changelog

All notable changes to this project will be documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
