"""The Ariston integration."""

from __future__ import annotations

import logging
import subprocess
import sys

import voluptuous as vol

# Required version - update this when releasing new versions
REQUIRED_ARISTON_VERSION = "0.19.9"

def _ensure_ariston_installed():
    """Ensure ariston library is installed, auto-upgrade if needed."""
    logger = logging.getLogger(__name__)
    
    try:
        import ariston
        from packaging import version
        
        current = getattr(ariston, '__version__', '0.0.0')
        required = REQUIRED_ARISTON_VERSION
        
        if version.parse(current) < version.parse(required):
            logger.info(f"Upgrading ariston from {current} to {required}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", f"ariston=={required}"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                logger.error(f"Pip install failed: {result.stderr}")
                raise RuntimeError(f"Failed to upgrade ariston: {result.stderr}")
            logger.info("Ariston library upgraded successfully")
        else:
            logger.debug(f"Ariston {current} already satisfies requirement >= {required}")
            
    except ImportError:
        logger.warning(f"Ariston library not found, installing ariston=={REQUIRED_ARISTON_VERSION}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", f"ariston=={REQUIRED_ARISTON_VERSION}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.error(f"Pip install failed: {result.stderr}")
            raise RuntimeError(f"Failed to install ariston: {result.stderr}")
        logger.info("Ariston library installed successfully")
    except Exception as err:
        logger.error(f"Failed to install/upgrade ariston: {err}")
        # Don't raise - let the import below fail with clear error
        logger.critical("Ariston dependency NOT available - integration will not load")

# Initialize ariston dependency SYNCHRONOUSLY before other imports
_ensure_ariston_installed()

try:
    from ariston import Ariston, DeviceAttribute, SystemType
    from ariston.ariston_api import ConnectionException
    from ariston.const import ARISTON_API_URL, ARISTON_USER_AGENT
    _ARISTON_AVAILABLE = True
except ImportError as err:
    _LOGGER = logging.getLogger(__name__)
    _LOGGER.critical("CRITICAL: Cannot import ariston library: %s", err)
    _LOGGER.critical("Check logs above for pip install errors. Integration cannot load.")
    _ARISTON_AVAILABLE = False
    # Define dummy classes to avoid NameError in async_setup_entry
    class Ariston: pass
    class DeviceAttribute: pass
    class SystemType: pass
    class ConnectionException(Exception): pass
    ARISTON_API_URL = ""
    ARISTON_USER_AGENT = ""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DEVICE_ID,
    CONF_DEVICE,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    API_URL_SETTING,
    API_USER_AGENT,
    BUS_ERRORS_COORDINATOR,
    BUS_ERRORS_SCAN_INTERVAL,
    COORDINATOR,
    DEFAULT_BUS_ERRORS_SCAN_INTERVAL_SECONDS,
    DEFAULT_ENERGY_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    ENERGY_COORDINATOR,
    ENERGY_SCAN_INTERVAL,
)
from .coordinator import DeviceDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.WATER_HEATER,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ariston component (required for HA to recognize the integration)."""
    # This is needed for HA to properly load the integration
    # The actual setup is done via config entries in async_setup_entry
    return True

SERVICE_SET_ITEM_BY_ID = "set_item_by_id"
ATTR_ITEM_ID = "item_id"
ATTR_ZONE = "zone"
ATTR_VALUE = "value"

SET_ITEM_BY_ID_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_ITEM_ID): cv.string,
        vol.Required(ATTR_ZONE): cv.positive_int,
        vol.Required(ATTR_VALUE): vol.Coerce(float),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ariston from a config entry."""
    if not _ARISTON_AVAILABLE:
        _LOGGER.error("Ariston library not available - cannot set up integration")
        return False
    
    ariston = Ariston()
    try:
        api_url_setting = entry.data.get(API_URL_SETTING, ARISTON_API_URL)

        api_user_agent = entry.data.get(API_USER_AGENT, ARISTON_USER_AGENT)

        reponse = await ariston.async_connect(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            api_url_setting,
            api_user_agent,
        )
        if not reponse:
            _LOGGER.error(
                "Failed to connect to Ariston with device: %s",
                entry.data[CONF_DEVICE].get(DeviceAttribute.NAME),
            )
            raise ConfigEntryAuthFailed

        device = await ariston.async_hello(
            entry.data[CONF_DEVICE].get(DeviceAttribute.GW),
            hass.config.units is METRIC_SYSTEM,
        )
        if device is None:
            return False

        await device.async_get_features()

        scan_interval_seconds = entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS
        )
        coordinator = DeviceDataUpdateCoordinator(
            hass, device, scan_interval_seconds, COORDINATOR, device.async_update_state
        )

        hass.data.setdefault(DOMAIN, {}).setdefault(
            entry.unique_id, {COORDINATOR: {}, ENERGY_COORDINATOR: {}}
        )
        hass.data[DOMAIN][entry.unique_id][COORDINATOR] = coordinator

        await coordinator.async_config_entry_first_refresh()

        bus_errors_scan_interval_seconds = entry.options.get(
            BUS_ERRORS_SCAN_INTERVAL, DEFAULT_BUS_ERRORS_SCAN_INTERVAL_SECONDS
        )
        bus_errors_coordinator = DeviceDataUpdateCoordinator(
            hass,
            device,
            bus_errors_scan_interval_seconds,
            BUS_ERRORS_COORDINATOR,
            device.async_get_bus_errors,
        )
        hass.data[DOMAIN][entry.unique_id][BUS_ERRORS_COORDINATOR] = (
            bus_errors_coordinator
        )
        # Bus errors are diagnostic data: a failing endpoint must not block setup.
        await bus_errors_coordinator.async_refresh()

        if device.has_metering:
            energy_interval_minutes = entry.options.get(
                ENERGY_SCAN_INTERVAL, DEFAULT_ENERGY_SCAN_INTERVAL_MINUTES
            )
            energy_coordinator = DeviceDataUpdateCoordinator(
                hass,
                device,
                energy_interval_minutes * 60,
                ENERGY_COORDINATOR,
                device.async_update_energy,
            )
            hass.data[DOMAIN][entry.unique_id][ENERGY_COORDINATOR] = energy_coordinator
            # Energy data is optional: do not fail setup if the endpoint is down.
            await energy_coordinator.async_refresh()

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        entry.async_on_unload(entry.add_update_listener(update_listener))

        if device.system_type == SystemType.GALEVO:

            async def async_set_item_by_id_service(service_call):
                """Create a vacation on the target device."""
                device_id = service_call.data.get(ATTR_DEVICE_ID)
                item_id = service_call.data.get(ATTR_ITEM_ID)
                zone = service_call.data.get(ATTR_ZONE)
                value = service_call.data.get(ATTR_VALUE)

                device_registry = dr.async_get(hass)
                device = device_registry.devices[device_id]

                entry = hass.config_entries.async_get_entry(
                    next(iter(device.config_entries))
                )
                coordinator: DeviceDataUpdateCoordinator = hass.data[DOMAIN][
                    entry.unique_id
                ][COORDINATOR]
                await coordinator.device.async_set_item_by_id(item_id, value, zone)

            hass.services.async_register(
                DOMAIN,
                SERVICE_SET_ITEM_BY_ID,
                async_set_item_by_id_service,
                schema=SET_ITEM_BY_ID_SCHEMA,
            )
    except ConfigEntryAuthFailed:
        raise
    except ConnectionException as error:
        _LOGGER.error("Connection error during setup: %s", error)
        raise ConfigEntryNotReady from error
    except Exception as error:
        _LOGGER.exception("Unexpected error during setup")
        raise ConfigEntryNotReady from error

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.unique_id)

    return unload_ok
