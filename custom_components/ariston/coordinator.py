from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import timedelta
from typing import Any

from ariston.ariston_api import ConnectionException
from ariston.base_device import AristonBaseDevice
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Retryable HTTP status codes
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
# Max retries for non-rate-limit errors
MAX_RETRIES = 3
# Base delay for retries (seconds)
BASE_RETRY_DELAY = 10


class DeviceDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Manages polling for state changes from the device."""

    def __init__(
        self,
        hass: HomeAssistant,
        device: AristonBaseDevice,
        scan_interval_seconds: int,
        coordinator_name: str,
        async_update_state: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{device.name}-{coordinator_name}",
            update_interval=timedelta(seconds=scan_interval_seconds),
            update_method=self._async_update_with_retry(async_update_state),
        )

        self.device = device
        self._rate_limit_delay = 0
        self._max_rate_limit_delay = 300  # 5 minutes max delay

    def _async_update_with_retry(
        self, async_update_state: Callable[[], Coroutine[Any, Any, None]]
    ):
        """Return an update method that handles rate limiting and retries with exponential backoff."""

        async def _wrapped_update() -> None:
            last_exception: Exception | None = None

            for attempt in range(MAX_RETRIES + 1):
                try:
                    await async_update_state()
                    # Success - reset rate limit delay on successful request
                    self._rate_limit_delay = 0
                    return
                except ConnectionException as err:
                    last_exception = err
                    status_code = err.args[0] if err.args else None

                    if status_code in RETRYABLE_STATUS_CODES:
                        if status_code == 429:
                            # Rate limited - exponential backoff with longer delays
                            self._rate_limit_delay = min(
                                self._rate_limit_delay * 2
                                if self._rate_limit_delay
                                else 60,
                                self._max_rate_limit_delay,
                            )
                            delay = self._rate_limit_delay
                            _LOGGER.warning(
                                "Rate limited by Ariston API (429), backing off for %d seconds (attempt %d/%d)",
                                delay,
                                attempt + 1,
                                MAX_RETRIES + 1,
                            )
                        else:
                            # Server errors - shorter exponential backoff
                            delay = min(BASE_RETRY_DELAY * (2**attempt), 60)
                            _LOGGER.warning(
                                "Ariston API server error (%s), retrying in %d seconds (attempt %d/%d)",
                                status_code,
                                delay,
                                attempt + 1,
                                MAX_RETRIES + 1,
                            )

                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(delay)
                            continue
                    # Non-retryable error or max retries exceeded
                    self._rate_limit_delay = 0
                    raise UpdateFailed(
                        f"Error communicating with Ariston API: {err}"
                    ) from err
                except asyncio.TimeoutError as err:
                    last_exception = err
                    _LOGGER.warning(
                        "Timeout communicating with Ariston API (attempt %d/%d)",
                        attempt + 1,
                        MAX_RETRIES + 1,
                    )
                    if attempt < MAX_RETRIES:
                        delay = min(BASE_RETRY_DELAY * (2**attempt), 60)
                        await asyncio.sleep(delay)
                        continue
                    self._rate_limit_delay = 0
                    raise UpdateFailed(
                        f"Timeout communicating with Ariston API: {err}"
                    ) from err
                except Exception as err:
                    # Unexpected errors - don't retry
                    self._rate_limit_delay = 0
                    _LOGGER.exception("Unexpected error communicating with Ariston API")
                    raise UpdateFailed(
                        f"Unexpected error communicating with Ariston API: {err}"
                    ) from err

            # All retries exhausted
            self._rate_limit_delay = 0
            raise UpdateFailed(
                f"Max retries exceeded communicating with Ariston API: {last_exception}"
            ) from last_exception

        return _wrapped_update
