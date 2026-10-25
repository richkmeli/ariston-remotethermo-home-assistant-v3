# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.20.7] - 2026-10-25

### Fixed
- **HACS install layout**: release assets now contain the integration files at the ZIP root instead of an extra `ariston/` folder. HACS extracts the asset into `custom_components/ariston`, so the old layout produced `custom_components/ariston/ariston/…` and Home Assistant could not find `__init__.py`/`manifest.json` ("No setup or config entry setup function defined").
- **Release workflow**: replaced the unmaintained upload action with `softprops/action-gh-release` and build the asset with `git archive` so the layout is deterministic.
- **CI artifact**: same flat ZIP layout as the release asset.

### Removed
- **Import-time `pip install`**: `__init__.py` no longer runs `pip` while Home Assistant imports the integration. This blocked startup for up to 60 s on every load (`ariston` does not expose `__version__`, so the check always ran) and could not fix a misplaced/missing module. Dependencies are installed by Home Assistant from `manifest.json`.

## [0.20.0] - 2025-10-25

### Fixed
- **strings.json**: Resolved placeholder references (`[%key:common::...%]`) with actual translatable strings for config flow UI
- **Device manufacturer**: Fixed `device_info` to report "Ariston" instead of domain string for proper device registry
- **Exception handling**: Replaced broad `except Exception` with specific `ConnectionException` handling in config flow and setup entry
- **Rate limiting**: Enhanced coordinator with retry logic for server errors (5xx), timeouts, and rate limits (429) with exponential backoff
- **Logging**: Improved error logging with context across all components

### Changed
- **Minimum Home Assistant version**: Raised from 2023.1.0 to 2024.1.0
- **Removed deprecated compatibility layer**: Dropped `WaterHeaterEntityEntityDescription` fallback (removed in HA 2025.1)
- **Coordinator resilience**: Added configurable retry attempts (3) with exponential backoff for transient failures

### Added
- **Type hints**: Added comprehensive type annotations across coordinator, config flow, and entity descriptions
- **CHANGELOG.md**: This file for version tracking

### Internal
- Code quality improvements: stricter typing, better error messages, consistent logging patterns

## [0.19.12] - Previous Release
- Initial fork release by @richkmeli
- Multi-coordinator architecture (main, bus errors, energy)
- Config flow with device discovery
- Support for GALEVO, BSB, VELIS system types
- Climate, Water Heater, Sensor, Binary Sensor, Switch, Number, Select platforms
- Custom services: `create_vacation`, `set_item_by_id`
- 9 language translations