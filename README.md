[![CodeQL](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/codeql.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HACS Action](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hacs.yml/badge.svg)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hacs.yml)
[![Validate with hassfest](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hassfest.yml/badge.svg)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hassfest.yml)
[![CI](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/ci.yml/badge.svg)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/ci.yml)
# Ariston NET remotethermo integration for Home Assistant
This is a fork of [fustom/ariston-remotethermo-home-assistant-v3](https://github.com/fustom/ariston-remotethermo-home-assistant-v3), maintained by [@richkmeli](https://github.com/richkmeli).
The original integration was inspired by chomupashchuk's work https://github.com/chomupashchuk/ariston-remotethermo-home-assistant-v2
It does not use the Ariston website: it uses the Ariston API reverse-engineered by the upstream project.


| [This fork](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3)  | [Chomupashchuk's v2 integration](https://github.com/chomupashchuk/ariston-remotethermo-home-assistant-v2) |
| ------------- | ------------- |
| Uses real API  | Uses Ariston website  |
| Faster set/get data  | Sometimes needs minutes to set/get data |
| Easy to set up with UI | Not so easy to set up (only with configuration.yaml) |
| Integration & devices & entities | Only entities |
| Proper asynchronous integration, clean code | Hard to understand and maintain (ariston.py has more than 4000 lines) |
| Less sensors, switches, etc |  More sensors, switches, etc |
| New code, may contain a lot of bugs | Old, tested code |

## Changelog v0.20.0
### Fixed
- **Config flow strings**: Resolved placeholder references in `strings.json` for proper UI translations
- **Device registry**: Fixed manufacturer name to "Ariston" for correct device identification
- **Exception handling**: Replaced broad exception catches with specific `ConnectionException` handling
- **Rate limiting**: Enhanced coordinator with retry logic for 429, 5xx errors, and timeouts with exponential backoff

### Changed
- **Minimum Home Assistant**: Raised from 2023.1 to 2024.1
- **Removed deprecated code**: Dropped `WaterHeaterEntityEntityDescription` compatibility layer
- **Type hints**: Added comprehensive type annotations across the codebase

### Added
- **Unit tests**: Basic test structure for coordinator and config flow (`tests/`)
- **CI/CD**: GitHub Actions workflow for testing, linting, and validation
- **CHANGELOG.md**: Version history tracking

### Internal
- Improved logging with context across all components
- Updated all 9 language translations (en, it, fr, es, pt, ru, ca, pl, ua)

## TODO
- [x] Localization. Available in English, Catalan, Italian, Russian, Ukrainian, French, Spanish, Portuguese, Polish.
- [ ] More sensors, switches, binary sensors, selectors, services.
- [x] Exception handling improvements.
- [ ] More detailed debug logging.
- [x] Unit tests (basic structure).
- [ ] Integration tests.
- [ ] Fun.

## Integration was tested on and works with:
- Ariston Alteas One 24
- Ariston Velis Evo
- Ariston Velis Lux
- Ariston Lydos Hybrid
- Ariston Genus One
- Ariston Nuos Split
- Ariston Thision S
- Chaffoteaux INOA S 24

Feel free to test something else and open an issue or pull request in this fork: https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/issues

## Installation
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=richkmeli&repository=ariston-remotethermo-home-assistant-v3&category=integration) or copy the `custom_components/ariston` folder to your configuration/custom_components path.
Use the add integration UI to set up your device.

> **Fork note:** HACS installs this fork from its releases. The release asset must contain the integration files at the ZIP root (no extra `ariston/` folder), because HACS extracts it directly into `custom_components/ariston`.

### Troubleshooting: integration disappeared after an update

If Home Assistant logs `No setup or config entry setup function defined` or the integration is no longer listed, check the installed layout:

```bash
ls /config/custom_components/ariston
```

You should see `__init__.py` and `manifest.json` directly in that folder. If there is another `ariston/` subfolder, a malformed release ZIP (v0.20.0–v0.20.6) was installed. With Home Assistant stopped, delete `custom_components/ariston`, install v0.20.8 or later from HACS, and restart.

> **Note:** releases v0.20.0–v0.20.7 also fail on Home Assistant versions older than 2025.1 because they import an API added in 2025.1. v0.20.8 restores compatibility.

| ![Kazam_screenshot_00003](https://user-images.githubusercontent.com/6751243/146653448-ff7b6f9d-cbf1-4555-9a75-61bf68bc9d3e.png) | ![Kazam_screenshot_00004](https://user-images.githubusercontent.com/6751243/146653484-52e39d78-7c6f-44ae-888d-acf246147290.png) | ![Kazam_screenshot_00010](https://user-images.githubusercontent.com/6751243/147890590-6c4ebf38-16d9-421f-9b81-8f43298ec62f.png) |
|:-------------------------:|:-------------------------:|:-------------------------:|

![Kazam_screenshot_00011](https://user-images.githubusercontent.com/6751243/147890611-54ae2d28-bf5a-45f8-ba92-e7a00a22615c.png)

![Kazam_screenshot_00012](https://user-images.githubusercontent.com/6751243/147989103-cdac510f-e6f6-461f-a88e-b8ff0204c34f.png)

| ![Kazam_screenshot_00013](https://user-images.githubusercontent.com/6751243/148247717-5211c01c-561f-4a4e-b4b5-47a680e04a68.png) | ![Kazam_screenshot_00009](https://user-images.githubusercontent.com/6751243/146657797-ed14b741-595a-48a6-9126-1acca3beb69f.png) |
|:-------------------------:|:-------------------------:|

<h1 align="center">Peace Love Freedom</h1>