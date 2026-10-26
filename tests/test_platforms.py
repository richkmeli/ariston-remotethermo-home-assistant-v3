"""Tests for the entity platforms (sensors, switches, binary sensors)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ariston.const import (
    CustomDeviceFeatures,
    EvoDeviceProperties,
    EvoLydosDeviceProperties,
    EvoOneDeviceProperties,
    SystemType,
    VelisDeviceProperties,
    WheType,
)
from homeassistant.components.water_heater import WaterHeaterEntityFeature

from custom_components.ariston import binary_sensor, sensor, switch, water_heater
from custom_components.ariston.const import (
    BUS_ERRORS_COORDINATOR,
    COORDINATOR,
    DOMAIN,
    ENERGY_COORDINATOR,
    INSTANTANEOUS_POWER_KEY,
)


@pytest.fixture
def device():
    """Create a VELIS Lux device that exposes the usual features."""
    device = MagicMock()
    device.system_type = SystemType.VELIS
    device.whe_type = WheType.Lux
    device.whe_model_type = 0
    device.name = "Boiler"
    device.gateway = "gw-test"
    device.serial_number = "sn-test"
    device.firmware_version = "1.0"
    device.features = {}
    device.custom_features = {CustomDeviceFeatures.HAS_DHW: True}
    device.attributes = {}
    device.dhw_mode_changeable = True
    device.water_heater_temperature_step = 1
    device.water_heater_power_value = True
    device.is_heating = True

    def _available(device_features=None, system_types=None, whe_types=None):
        if system_types and device.system_type not in system_types:
            return False
        if whe_types and device.whe_type not in whe_types:
            return False
        for feature in device_features or []:
            if not (
                device.features.get(feature)
                or device.custom_features.get(feature)
                or device.attributes.get(feature)
            ):
                return False
        return True

    device.are_device_features_available.side_effect = _available
    return device


@pytest.fixture
def coordinator(device):
    """Create a coordinator exposing the mock device."""
    coordinator = MagicMock()
    coordinator.device = device
    coordinator.rated_power_w = None
    coordinator.config_entry.options = {}
    return coordinator


@pytest.fixture
def hass(coordinator):
    """Create a minimal Home Assistant object with the integration data."""
    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "entry-id": {
                COORDINATOR: coordinator,
                ENERGY_COORDINATOR: coordinator,
                BUS_ERRORS_COORDINATOR: coordinator,
            }
        }
    }
    return hass


@pytest.fixture
def entry():
    """Create a minimal config entry."""
    entry = MagicMock()
    entry.unique_id = "entry-id"
    entry.options = {}
    return entry


def _created(async_add_entities) -> list:
    return async_add_entities.call_args.args[0]


async def test_sensor_setup_creates_velis_entities(hass, entry, coordinator):
    """VELIS sensors are created, metering sensors are not."""
    async_add_entities = MagicMock()

    await sensor.async_setup_entry(hass, entry, async_add_entities)

    keys = [entity.entity_description.key for entity in _created(async_add_entities)]
    assert EvoOneDeviceProperties.TEMP in keys
    assert EvoLydosDeviceProperties.REQ_TEMP in keys
    assert EvoDeviceProperties.RM_TM in keys
    # No metering feature on this device.
    assert "Domestic hot water electricity consumption" not in keys


async def test_power_sensor_requires_rated_power(hass, entry, coordinator):
    """The estimated power sensor is only created when rated power is set."""
    async_add_entities = MagicMock()

    await sensor.async_setup_entry(hass, entry, async_add_entities)
    keys = [entity.entity_description.key for entity in _created(async_add_entities)]
    assert INSTANTANEOUS_POWER_KEY not in keys

    coordinator.rated_power_w = 1500
    async_add_entities.reset_mock()

    await sensor.async_setup_entry(hass, entry, async_add_entities)
    keys = [entity.entity_description.key for entity in _created(async_add_entities)]
    assert INSTANTANEOUS_POWER_KEY in keys


async def test_binary_sensor_setup_includes_anti_legionella(hass, entry):
    """Lux/Lux2 expose both heating and anti-legionella binary sensors."""
    async_add_entities = MagicMock()

    await binary_sensor.async_setup_entry(hass, entry, async_add_entities)

    keys = [entity.entity_description.key for entity in _created(async_add_entities)]
    assert EvoLydosDeviceProperties.HEAT_REQ in keys
    assert EvoLydosDeviceProperties.ANTI_LEG in keys


async def test_switch_setup_includes_power(hass, entry):
    """The VELIS power switch is created."""
    async_add_entities = MagicMock()

    await switch.async_setup_entry(hass, entry, async_add_entities)

    keys = [entity.entity_description.key for entity in _created(async_add_entities)]
    assert VelisDeviceProperties.ON in keys


async def test_water_heater_setup_and_attributes(hass, entry):
    """The water heater is created and reports power/heating attributes."""
    async_add_entities = MagicMock()

    await water_heater.async_setup_entry(hass, entry, async_add_entities)

    entities = _created(async_add_entities)
    assert len(entities) == 1
    entity = entities[0]
    assert entity.supported_features & WaterHeaterEntityFeature.ON_OFF

    attributes = entity.extra_state_attributes
    assert attributes["power"] == "on"
    assert attributes["heating"] is True
