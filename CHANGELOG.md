# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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