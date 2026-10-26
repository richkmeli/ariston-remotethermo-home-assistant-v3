"""Diagnostics support for the Ariston integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import BUS_ERRORS_COORDINATOR, COORDINATOR, DOMAIN, ENERGY_COORDINATOR

# Credentials, gateway identifiers and plant geolocation must never leave the
# user's instance when a diagnostics dump is attached to an issue.
TO_REDACT = {
    "username",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "gw",
    "gateway",
    "sn",
    "serial_number",
    "loc",
}


def _device_diagnostics(device: Any) -> dict[str, Any]:
    """Return the device state in a JSON-serialisable form."""
    return {
        "name": getattr(device, "name", None),
        "system_type": getattr(getattr(device, "system_type", None), "name", None),
        "whe_type": getattr(getattr(device, "whe_type", None), "name", None),
        "whe_model_type": getattr(device, "whe_model_type", None),
        "firmware_version": getattr(device, "firmware_version", None),
        "attributes": getattr(device, "attributes", {}),
        "features": getattr(device, "features", {}),
        "custom_features": getattr(device, "custom_features", {}),
        "plant_settings": getattr(device, "plant_settings", None),
        "data": getattr(device, "data", {}),
        "consumptions_sequences": getattr(device, "consumptions_sequences", None),
        "bus_errors": getattr(device, "bus_errors_list", None),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.unique_id, {})

    diagnostics: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinators": {},
    }

    for coordinator_name in (COORDINATOR, ENERGY_COORDINATOR, BUS_ERRORS_COORDINATOR):
        coordinator = entry_data.get(coordinator_name)
        if coordinator is None or getattr(coordinator, "device", None) is None:
            continue

        diagnostics["coordinators"][coordinator_name] = {
            "last_update_success": getattr(coordinator, "last_update_success", None),
            "last_exception": repr(getattr(coordinator, "last_exception", None)),
            "device": _device_diagnostics(coordinator.device),
        }

    return async_redact_data(diagnostics, TO_REDACT)
