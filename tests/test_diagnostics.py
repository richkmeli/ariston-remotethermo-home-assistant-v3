"""Tests for the diagnostics dump."""

from __future__ import annotations

from unittest.mock import MagicMock

from ariston.const import SystemType, WheType

from custom_components.ariston.const import COORDINATOR, DOMAIN, ENERGY_COORDINATOR
from custom_components.ariston.diagnostics import (
    async_get_config_entry_diagnostics,
)


def _entry():
    entry = MagicMock()
    entry.unique_id = "entry-id"
    entry.title = "Ariston"
    entry.data = {
        "username": "user@example.com",
        "password": "secret",
        "device": {"gw": "gateway-id", "sn": "serial-id", "name": "Boiler"},
    }
    entry.options = {"scan_interval": 300}
    return entry


def _coordinator():
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.last_exception = None
    coordinator.device.name = "Boiler"
    coordinator.device.system_type = SystemType.VELIS
    coordinator.device.whe_type = WheType.Lux
    coordinator.device.whe_model_type = 0
    coordinator.device.firmware_version = "1.0"
    coordinator.device.attributes = {"gw": "gateway-id", "sn": "serial-id"}
    coordinator.device.features = {"hasMetering": False}
    coordinator.device.custom_features = {}
    coordinator.device.plant_settings = {"MedMaxSetpointTemperature": 60}
    coordinator.device.data = {"temp": 55}
    coordinator.device.consumptions_sequences = []
    coordinator.device.bus_errors_list = []
    return coordinator


async def test_diagnostics_redacts_identifiers():
    """Credentials and device identifiers are redacted from the dump."""
    entry = _entry()
    coordinator = _coordinator()
    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            entry.unique_id: {
                COORDINATOR: coordinator,
                ENERGY_COORDINATOR: coordinator,
            }
        }
    }

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["data"]["username"] == "**REDACTED**"
    assert result["entry"]["data"]["password"] == "**REDACTED**"
    assert result["entry"]["data"]["device"]["gw"] == "**REDACTED**"
    assert result["entry"]["data"]["device"]["sn"] == "**REDACTED**"
    assert result["entry"]["data"]["device"]["name"] == "Boiler"
    assert result["entry"]["options"]["scan_interval"] == 300

    device = result["coordinators"][COORDINATOR]["device"]
    assert device["whe_type"] == "Lux"
    assert device["plant_settings"] == {"MedMaxSetpointTemperature": 60}
    assert device["attributes"]["gw"] == "**REDACTED**"
    assert device["attributes"]["sn"] == "**REDACTED**"


async def test_diagnostics_without_coordinators():
    """A not-yet-loaded entry still returns the redacted entry data."""
    entry = _entry()
    hass = MagicMock()
    hass.data = {DOMAIN: {}}

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["coordinators"] == {}
    assert result["entry"]["data"]["password"] == "**REDACTED**"
