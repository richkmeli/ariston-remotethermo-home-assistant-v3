[![CodeQL](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/codeql.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HACS Action](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hacs.yml/badge.svg)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hacs.yml)
[![Validate with hassfest](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hassfest.yml/badge.svg)](https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/actions/workflows/hassfest.yml)
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

## TODO
- Localization. Available in English, Catalan, Italian, Russian and Ukrainian.
- More sensors, switches, binary sensors, selectors, services.
- Exception handling.
- More logs.
- Unit tests.
- Fun.

## Integration was tested on and works with:
- Ariston Alteas One 24
- Ariston Velis Evo
- Ariston Velis Lux
- Ariston Lydos Hybrid

Feel free to test something else and open an issue or pull request in this fork: https://github.com/richkmeli/ariston-remotethermo-home-assistant-v3/issues

## Installation
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=richkmeli&repository=ariston-remotethermo-home-assistant-v3&category=integration) or copy the `custom_components/ariston` folder to your configuration/custom_components path.
Use the add integration UI to set up your device.

> **Fork note:** HACS installs this fork only when a release with the `ariston-remotethermo-home-assistant-v3.zip` asset is published. Until then, install it manually by copying `custom_components/ariston` into your Home Assistant configuration.

| ![Kazam_screenshot_00003](https://user-images.githubusercontent.com/6751243/146653448-ff7b6f9d-cbf1-4555-9a75-61bf68bc9d3e.png) | ![Kazam_screenshot_00004](https://user-images.githubusercontent.com/6751243/146653484-52e39d78-7c6f-44ae-888d-acf246147290.png) | ![Kazam_screenshot_00010](https://user-images.githubusercontent.com/6751243/147890590-6c4ebf38-16d9-421f-9b81-8f43298ec62f.png) |
:-------------------------:|:-------------------------:|:-------------------------:

![Kazam_screenshot_00011](https://user-images.githubusercontent.com/6751243/147890611-54ae2d28-bf5a-45f8-ba92-e7a00a22615c.png)

![Kazam_screenshot_00012](https://user-images.githubusercontent.com/6751243/147989103-cdac510f-e6f6-461f-a88e-b8ff0204c34f.png)

| ![Kazam_screenshot_00013](https://user-images.githubusercontent.com/6751243/148247717-5211c01c-561f-4a4e-b4b5-47a680e04a68.png) | ![Kazam_screenshot_00009](https://user-images.githubusercontent.com/6751243/146657797-ed14b741-595a-48a6-9126-1acca3beb69f.png) |
:-------------------------:|:-------------------------:

<h1 align="center">Peace Love Freedom</h1>
