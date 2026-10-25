"""Support for Ariston water heaters."""

from __future__ import annotations

import logging

from ariston.const import SystemType
from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from .const import (
    ARISTON_WATER_HEATER_TYPES,
    CONF_WATER_HEATER_TEMPERATURE_UNIT_OVERRIDE,
    DOMAIN,
    NAME,
    AristonWaterHeaterEntityDescription,
)
from .coordinator import DeviceDataUpdateCoordinator, PendingWrite
from .entity import AristonEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the Ariston water heater device from config entry."""
    ariston_water_heaters: list[AristonWaterHeater] = []
    for description in ARISTON_WATER_HEATER_TYPES:
        coordinator: DeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.unique_id][
            description.coordinator
        ]

        if (
            coordinator
            and coordinator.device
            and coordinator.device.are_device_features_available(
                description.device_features,
                description.system_types,
                description.whe_types,
            )
        ):
            ariston_water_heaters.append(AristonWaterHeater(coordinator, description))

    async_add_entities(ariston_water_heaters)


class AristonWaterHeater(AristonEntity, WaterHeaterEntity):
    """Ariston Water Heater Device."""

    def __init__(
        self,
        coordinator: DeviceDataUpdateCoordinator,
        description: AristonWaterHeaterEntityDescription,
    ) -> None:
        """Initialize the water heater."""
        super().__init__(coordinator, description)
        self._temp_unit_override = self.coordinator.config_entry.options.get(
            CONF_WATER_HEATER_TEMPERATURE_UNIT_OVERRIDE, "auto"
        )

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.device.name or NAME

    @property
    def unique_id(self) -> str:
        """Return a unique id for the device."""
        return f"{self.device.gateway}-water_heater"

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:water-pump"

    @property
    def current_temperature(self):
        """Return the temperature."""
        temp = self.device.water_heater_current_temperature
        return self._convert_temp(temp)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        temp = self.device.water_heater_minimum_temperature
        return self._convert_temp(temp)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        temp = self.device.water_heater_target_temperature
        return self._convert_temp(temp)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        temp = self.device.water_heater_maximum_temperature
        return self._convert_temp(temp)

    @property
    def precision(self) -> float:
        """Return the precision of temperature for the device."""
        return 1 / 10**self.device.water_heater_temperature_decimals

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._temp_unit_override == "celsius":
            return UnitOfTemperature.CELSIUS
        if self._temp_unit_override == "fahrenheit":
            return UnitOfTemperature.FAHRENHEIT
        return self.device.water_heater_temperature_unit

    def _convert_temp(self, temp):
        """Convert temperature based on override setting."""
        if temp is None:
            return None
        if self._temp_unit_override == "auto":
            return temp
        device_unit = self.device.water_heater_temperature_unit
        if (
            self._temp_unit_override == "celsius"
            and device_unit == UnitOfTemperature.FAHRENHEIT
        ):
            return (temp - 32) * 5 / 9
        if (
            self._temp_unit_override == "fahrenheit"
            and device_unit == UnitOfTemperature.CELSIUS
        ):
            return temp * 9 / 5 + 32
        return temp

    @property
    def supported_features(self) -> int:
        """Return the supported features for this device integration."""
        features = WaterHeaterEntityFeature.TARGET_TEMPERATURE
        if self.device.dhw_mode_changeable:
            features |= WaterHeaterEntityFeature.OPERATION_MODE
        if (
            self.device.system_type == SystemType.VELIS
            and "ON_OFF"
            in WaterHeaterEntityFeature.__members__  # check entity feature for backward compatibility
        ):
            features |= WaterHeaterEntityFeature.ON_OFF
        return features

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self.device.water_heater_mode_operation_texts

    @property
    def current_operation(self):
        """Return current operation."""
        return self.device.water_heater_current_mode_text

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE not in kwargs:
            raise ValueError(f"Missing parameter {ATTR_TEMPERATURE}")

        temperature = kwargs[ATTR_TEMPERATURE]
        _LOGGER.debug(
            "Setting temperature to %d for %s",
            temperature,
            self.name,
        )

        # Convert temperature back to device's native unit if override is set
        device_temp = self._convert_temp_back(temperature)
        await self.device.async_set_water_heater_temperature(device_temp)
        # In BOOST the device enforces its own setpoint, so verifying the
        # requested temperature would just trigger pointless retries.
        if self.current_operation != "BOOST":
            self.coordinator.pending_writes["temperature"] = PendingWrite(
                prop="temperature", expected=device_temp
            )
        self.async_write_ha_state()

    def _convert_temp_back(self, temp):
        """Convert temperature from override unit back to device's native unit."""
        if temp is None:
            return None
        if self._temp_unit_override == "auto":
            return temp
        device_unit = self.device.water_heater_temperature_unit
        if (
            self._temp_unit_override == "celsius"
            and device_unit == UnitOfTemperature.FAHRENHEIT
        ):
            return temp * 9 / 5 + 32
        if (
            self._temp_unit_override == "fahrenheit"
            and device_unit == UnitOfTemperature.CELSIUS
        ):
            return (temp - 32) * 5 / 9
        return temp

    async def async_set_operation_mode(self, operation_mode):
        """Set operation mode."""
        await self.device.async_set_water_heater_operation_mode(operation_mode)
        self.coordinator.pending_writes["operation_mode"] = PendingWrite(
            prop="operation_mode", expected=operation_mode
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the water heater off."""
        await self.device.async_set_power(False)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the water heater on."""
        await self.device.async_set_power(True)
