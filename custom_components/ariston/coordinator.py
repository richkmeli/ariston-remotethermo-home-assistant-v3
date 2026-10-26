from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from ariston.ariston_api import ConnectionException
from ariston.base_device import AristonBaseDevice
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Retryable HTTP status codes
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
# Max retries for non-rate-limit errors
MAX_RETRIES = 3
# Base delay for retries (seconds)
BASE_RETRY_DELAY = 10
# How often the (rarely changing) plant settings are refreshed
SETTINGS_REFRESH_INTERVAL = timedelta(minutes=10)

# Write prop -> (device attribute holding the confirmed value,
#                device method that (re)issues the write)
DEVICE_WRITE_PROPS: dict[str, tuple[str, str]] = {
    "temperature": (
        "water_heater_target_temperature",
        "async_set_water_heater_temperature",
    ),
    "operation_mode": (
        "water_heater_current_mode_text",
        "async_set_water_heater_operation_mode",
    ),
    "power": (
        "water_heater_power_value",
        "async_set_power",
    ),
}


@dataclass
class PendingWrite:
    """A write whose effect still has to show up in a regular poll."""

    prop: str
    expected: Any
    tries: int = 0
    max_tries: int = 3


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
            update_method=self._async_update_and_verify,
        )

        self.device = device
        self.coordinator_name = coordinator_name
        self._async_device_update = self._async_update_with_retry(async_update_state)
        self._rate_limit_delay = 0
        self._max_rate_limit_delay = 300  # 5 minutes max delay
        self.pending_writes: dict[str, PendingWrite] = {}
        self.rated_power_w: int | None = None
        self._last_settings_refresh: datetime | None = None

    async def _async_update_and_verify(self) -> None:
        """Poll the device, refresh settings and verify pending writes.

        Verification rides on the regular poll, so no extra API reads are
        needed. Settings are read from a separate endpoint and are refreshed
        at most every :data:`SETTINGS_REFRESH_INTERVAL`.
        """
        await self._async_device_update()
        # Only the main coordinator owns plant settings and entity writes.
        if self.coordinator_name != COORDINATOR:
            return
        await self._async_refresh_settings()
        await self._async_check_pending_writes()

    async def _async_refresh_settings(self) -> None:
        """Refresh plant settings without making the poll fail.

        ``async_update_state`` only refreshes the plant data. Setpoint limits,
        anti-legionella and similar values live in ``plant_settings`` and would
        otherwise stay frozen until the config entry is reloaded.
        """
        update_settings = getattr(self.device, "async_update_settings", None)
        if update_settings is None:
            return

        now = datetime.now(UTC)
        if (
            self._last_settings_refresh is not None
            and now - self._last_settings_refresh < SETTINGS_REFRESH_INTERVAL
        ):
            return

        self._last_settings_refresh = now
        try:
            await update_settings()
        except Exception as err:  # noqa: BLE001 - settings are optional
            _LOGGER.debug("Unable to refresh %s settings: %s", self.name, err)

    async def _async_check_pending_writes(self) -> None:
        """Check pending writes against freshly polled device state.

        Match: clear. Mismatch with tries left: write again. Out of tries:
        warn and give up, so verification can never become a write loop.
        """
        for prop, pending in list(self.pending_writes.items()):
            accessors = DEVICE_WRITE_PROPS.get(prop)
            if accessors is None:
                _LOGGER.warning(
                    "No verification accessor for pending write %s; dropping it",
                    prop,
                )
                del self.pending_writes[prop]
                continue

            read_attr, write_attr = accessors
            try:
                actual = getattr(self.device, read_attr)
            except (AttributeError, NameError):
                # Device type does not expose this property.
                del self.pending_writes[prop]
                continue

            if actual == pending.expected:
                del self.pending_writes[prop]
                continue

            if pending.tries >= pending.max_tries:
                _LOGGER.warning(
                    "Write verification for %s gave up after %s tries "
                    "(device stayed at %s, expected %s)",
                    prop,
                    pending.max_tries,
                    actual,
                    pending.expected,
                )
                del self.pending_writes[prop]
                continue

            pending.tries += 1
            try:
                await getattr(self.device, write_attr)(pending.expected)
            except Exception as err:  # noqa: BLE001 - a failed retry must never kill polling
                _LOGGER.warning(
                    "Retry write for %s failed (%s); trying again next poll",
                    prop,
                    err,
                )

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
