from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta

from ariston.ariston_api import ConnectionException
from ariston.base_device import AristonBaseDevice
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DeviceDataUpdateCoordinator(DataUpdateCoordinator):
    """Manages polling for state changes from the device."""

    def __init__(
        self,
        hass: HomeAssistant,
        device: AristonBaseDevice,
        scan_interval_seconds: int,
        coordinator_name: str,
        async_update_state: Callable,
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{device.name}-{coordinator_name}",
            update_interval=timedelta(seconds=scan_interval_seconds),
            update_method=self._async_update_with_rate_limit(async_update_state),
        )

        self.device = device
        self._rate_limit_delay = 0
        self._max_rate_limit_delay = 300  # 5 minutes max delay

    async def _async_update_with_rate_limit(self, async_update_state):
        """Wrapper that handles rate limiting with exponential backoff."""
        while True:
            try:
                return await async_update_state()
            except ConnectionException as err:
                if err.args and err.args[0] == 429:
                    # Rate limited - apply exponential backoff
                    self._rate_limit_delay = min(
                        self._rate_limit_delay * 2 if self._rate_limit_delay else 60,
                        self._max_rate_limit_delay,
                    )
                    _LOGGER.warning(
                        "Rate limited by Ariston API, backing off for %d seconds",
                        self._rate_limit_delay,
                    )
                    await asyncio.sleep(self._rate_limit_delay)
                    continue
                # For other errors (including 500), reset delay and re-raise
                self._rate_limit_delay = 0
                raise UpdateFailed(f"Error communicating with Ariston API: {err}") from err
            except Exception as err:
                self._rate_limit_delay = 0
                raise UpdateFailed(f"Error communicating with Ariston API: {err}") from err
