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

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history. Recent highlights:

- **v0.20.11**: daily energy totals, diagnostics download, water heater `power`/`heating` attributes, operation mode select for all VELIS.
- **v0.20.10**: anti-legionella sensor on Lux/Lux2, verified power writes, resilient setup when the settings endpoint is down.
- **v0.20.9**: estimated power and water temperature sensors, write verification, periodic plant settings refresh.

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

### Estimated power and temperature sensors (v0.20.9)

For VELIS water heaters (Velis Evo/Evo2, Lydos, Lydos Hybrid, Lux/Lux2, Andris2) the integration now provides:

- **Instantaneous power**: estimated from the heating state and the rated power configured in the integration options. For a Velis Tech 100 set `1500` W; leave the field empty to keep the sensor disabled.
- **Current water temperature** and **target water temperature** sensors, in addition to the values already exposed by the water heater entity.
- **Verified writes**: target temperature, operation mode and power are checked against the next poll and re-sent up to three times if the cloud silently ignored them.
- **Live plant settings**: limit, anti-legionella and similar configuration entities are refreshed every 10 minutes instead of only at startup. The integration also keeps working if the settings endpoint is temporarily unavailable.

### Energy Dashboard (v0.20.11)

The cloud only reports energy in hourly buckets, so the integration exposes **today's total** for each consumption counter. The value is the sum of the hourly samples and **resets at local midnight**: this is what the Energy Dashboard expects from a `total` sensor.

- If your model reports metering, the `... energy consumption` / `... electricity consumption` sensors can be added directly to **Settings → Dashboards → Energy**.
- The **instantaneous power** sensor is not an energy counter. To use it in the Energy Dashboard, create a **Riemann sum integral** helper (*Settings → Devices & services → Helpers*), with the power sensor as input, and add the resulting kWh sensor to the dashboard. The value is an estimate: it uses the rated power while the boiler is heating and zero otherwise.

### Water heater state and the power switch

`water_heater.ariston` reports the **operation mode** as its state (`MANUAL`, `PROGRAM`, `BOOST`, …). When the boiler is switched off, Home Assistant keeps showing the last mode instead of `off`; this is how the water heater platform works, not a bug in the integration.

Use `switch.ariston_power` when you need a reliable on/off state for dashboards or automations:

```yaml
action: switch.turn_off
target:
  entity_id: switch.ariston_power
```

Since v0.20.10 both `switch.ariston_power` and `water_heater.turn_on`/`turn_off` call the same API, and the switch state is refreshed immediately after either call.

### Example automations

**BOOST while the photovoltaic system is producing excess power.** `BOOST` is available on Lux/Lux2 (Velis Tech) and raises the setpoint to the maximum; the boiler returns to the previous mode when the boost ends.

```yaml
automation:
  - alias: "Ariston BOOST on solar surplus"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.solar_export_power
        above: 1200
        for: "00:10:00"
    actions:
      - action: water_heater.set_operation_mode
        target:
          entity_id: water_heater.ariston
        data:
          operation_mode: BOOST

  - alias: "Ariston back to PROGRAM"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.solar_export_power
        below: 200
        for: "00:10:00"
    actions:
      - action: water_heater.set_operation_mode
        target:
          entity_id: water_heater.ariston
        data:
          operation_mode: PROGRAM
```

Replace `sensor.solar_export_power` with your inverter/energy sensor. Check the exact entity IDs in **Developer tools → States**, because the water heater entity may not be `water_heater.ariston` if you renamed the device.

**Notify when the tank gets cold.**

```yaml
automation:
  - alias: "Ariston water temperature low"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.ariston_current_temperature
        below: 40
        for: "00:15:00"
    actions:
      - action: notify.persistent_notification
        data:
          title: "Ariston"
          message: "Water temperature below 40 °C."
```

### Diagnostics

If something does not work, download a diagnostics dump from **Settings → Devices & services → Ariston → ⋮ → Download diagnostics** and attach it to the issue. Credentials, gateway IDs and geolocation are redacted automatically; the dump contains device type, features, plant settings, raw state and consumption sequences.


| ![Kazam_screenshot_00003](https://user-images.githubusercontent.com/6751243/146653448-ff7b6f9d-cbf1-4555-9a75-61bf68bc9d3e.png) | ![Kazam_screenshot_00004](https://user-images.githubusercontent.com/6751243/146653484-52e39d78-7c6f-44ae-888d-acf246147290.png) | ![Kazam_screenshot_00010](https://user-images.githubusercontent.com/6751243/147890590-6c4ebf38-16d9-421f-9b81-8f43298ec62f.png) |
|:-------------------------:|:-------------------------:|:-------------------------:|

![Kazam_screenshot_00011](https://user-images.githubusercontent.com/6751243/147890611-54ae2d28-bf5a-45f8-ba92-e7a00a22615c.png)

![Kazam_screenshot_00012](https://user-images.githubusercontent.com/6751243/147989103-cdac510f-e6f6-461f-a88e-b8ff0204c34f.png)

| ![Kazam_screenshot_00013](https://user-images.githubusercontent.com/6751243/148247717-5211c01c-561f-4a4e-b4b5-47a680e04a68.png) | ![Kazam_screenshot_00009](https://user-images.githubusercontent.com/6751243/146657797-ed14b741-595a-48a6-9126-1acca3beb69f.png) |
|:-------------------------:|:-------------------------:|

<h1 align="center">Peace Love Freedom</h1>