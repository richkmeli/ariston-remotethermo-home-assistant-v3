# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.20.12] - 2026-10-26

### Changed
- **Water heater icon**: the `water_heater` entity now uses `mdi:water-boiler` instead of `mdi:water-pump`, so it is visually consistent with a boiler and with the power switch used in floor plans.
- **Documentation**: added a picture-elements example showing how to drive the floor-plan icon from `switch.ariston_power` (on/off colour) while keeping `water_heater.ariston` for modes and temperatures.

## [0.20.11] - 2026-10-26

### Added
- **Diagnostics download**: *Settings → Devices & services → Ariston → Download diagnostics* now includes device type, features, plant settings, raw state and consumption sequences. Credentials, gateway IDs and geolocation are redacted automatically.
- **Power and heating attributes** on the `water_heater` entity, so dashboards and templates can read the on/off state and the heating state without cross-referencing other entities.
- **Operation mode `select`** is now created for all VELIS models, not only Evo One. It exposes the same modes as the water heater card and is convenient for `select.select_option` automations.
- **Documentation**: Energy Dashboard setup, BOOST/anti-legionella automation examples, diagnostics instructions and the water heater state limitation.

### Fixed
- **Energy consumption sensors now report today's total.** The cloud returns one value per hour for the current day, but the upstream library only returns the last sample (usually zero). The integration now sums the hourly series and resets the counter at local midnight, so the Energy Dashboard receives a correct daily total. This also stops the `Detected new cycle ... last_reset 1970` log spam (upstream issues #439, #484, #486).

## [0.20.10] - 2026-10-26

### Added
- **Anti-legionella cycle binary sensor** is now created for Lux and Lux2 water heaters too (previously only Evo2, Lydos, Lydos Hybrid and Andris2). It shows when the boiler is running the high-temperature anti-legionella cycle.
- **Remaining time sensor** is now also created for Andris2 devices, which expose the same `rmTm` value.

### Fixed
- **Power writes are verified**: switching the water heater on/off (both `water_heater.turn_on`/`turn_off` and the `power` switch) is now checked against the next poll and retried up to three times if the cloud silently ignored it.
- **Immediate power state update**: `water_heater.turn_on`/`turn_off` now refresh the `power` switch immediately instead of waiting for the next poll.
- **Setup no longer fails when the plant-settings endpoint is down**: VELIS devices load their settings inside `async_get_features()`. A temporary HTTP error on that endpoint is now logged and retried by the coordinator, instead of blocking the whole integration setup (upstream issue #455).

## [0.20.9] - 2026-10-26

### Added
- **Estimated instantaneous power sensor** for VELIS water heaters (Evo, Evo2, Lydos, Lydos Hybrid, Lux, Lux2, Andris2). The Ariston API does not report electrical power directly, so the sensor uses the heating state (`is_heating`) and a configurable rated power. Set it in the integration options (e.g. `1500` W for a Velis Tech 100); leave it empty to keep the sensor disabled. Useful for the Home Assistant Energy Dashboard.
- **Current and target water temperature sensors** for all VELIS water heaters, exposing the same values as the water heater entity to history, statistics and automations.
- **Options translations**: the new rated power option is translated in all bundled languages.

### Fixed
- **Writes are now verified**: after setting the target temperature or the operation mode, the value is checked against the next poll and re-sent up to three times if the cloud silently ignored it. Temperature writes issued while in `BOOST` are skipped on purpose, because the device enforces its own setpoint in that mode.
- **Stale configuration entities**: plant settings (max setpoint, anti-legionella and similar number/switch entities) are now refreshed periodically (every 10 minutes) instead of only at setup, fixing entities that kept the startup values forever (upstream issue #487).

### Internal
- Coordinator gained `pending_writes`, `rated_power_w` and a non-fatal `async_update_settings()` refresh.

## [0.20.8] - 2026-10-25

### Fixed
- **Home Assistant < 2025.1 startup**: `const.py` imported `WaterHeaterEntityDescription` from `homeassistant.components.water_heater`, but that class only exists since Home Assistant 2025.1. On older versions (including 2024.x) the integration failed to import, so Home Assistant reported `No setup or config entry setup function defined` and the integration disappeared. `AristonWaterHeaterEntityDescription` now only inherits from `AristonBaseEntityDescription`, which works on every supported release.
- **Code formatting**: formatted the integration with `ruff format`.

### Internal
- CI lint now uses valid ruff selectors and the codebase passes `ruff format --check`.

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