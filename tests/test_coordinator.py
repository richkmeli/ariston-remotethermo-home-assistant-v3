"""Tests for DeviceDataUpdateCoordinator."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ariston.ariston_api import ConnectionException
from ariston.base_device import AristonBaseDevice

from custom_components.ariston.coordinator import DeviceDataUpdateCoordinator


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    """Skip real backoff delays so the retry tests run instantly."""

    async def _sleep(_delay):
        return None

    monkeypatch.setattr("asyncio.sleep", _sleep)


@pytest.fixture
async def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.loop = asyncio.get_running_loop()
    return hass


@pytest.fixture
def mock_device():
    """Create a mock Ariston device."""
    device = MagicMock(spec=AristonBaseDevice)
    device.name = "Test Device"
    device.gateway = "test-gateway"
    return device


@pytest.fixture
def coordinator(mock_hass, mock_device):
    """Create a coordinator instance."""

    async def mock_update():
        pass

    return DeviceDataUpdateCoordinator(
        hass=mock_hass,
        device=mock_device,
        scan_interval_seconds=300,
        coordinator_name="test",
        async_update_state=mock_update,
    )


async def test_coordinator_initialization(coordinator, mock_device):
    """Test coordinator initialization."""
    assert coordinator.device == mock_device
    assert coordinator.name == "ariston-Test Device-test"
    assert coordinator.update_interval.total_seconds() == 300


async def test_coordinator_rate_limit_backoff(coordinator, mock_device):
    """Test exponential backoff on rate limit (429)."""
    call_count = 0

    async def mock_update_rate_limited():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ConnectionException(429)
        return None

    coordinator.update_method = coordinator._async_update_with_retry(
        mock_update_rate_limited
    )

    # Should succeed on third attempt
    await coordinator.async_refresh()

    assert call_count == 3
    assert coordinator._rate_limit_delay == 0  # Reset on success


async def test_coordinator_server_error_retry(coordinator, mock_device):
    """Test retry on server errors (500, 502, 503, 504)."""
    call_count = 0

    async def mock_update_server_error():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ConnectionException(503)
        return None

    coordinator.update_method = coordinator._async_update_with_retry(
        mock_update_server_error
    )

    # Should succeed on third attempt
    await coordinator.async_refresh()

    assert call_count == 3


async def test_coordinator_max_retries_exceeded(coordinator, mock_device):
    """Test that failures are reported after max retries."""

    call_count = 0

    async def mock_update_always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionException(500)

    coordinator.update_method = coordinator._async_update_with_retry(
        mock_update_always_fails
    )

    # DataUpdateCoordinator swallows UpdateFailed and exposes it via state.
    await coordinator.async_refresh()

    assert call_count == 4  # initial attempt + MAX_RETRIES
    assert coordinator.last_update_success is False
    assert "500" in str(coordinator.last_exception)


async def test_coordinator_non_retryable_error(coordinator, mock_device):
    """Test non-retryable errors are not retried."""

    call_count = 0

    async def mock_update_auth_error():
        nonlocal call_count
        call_count += 1
        raise ConnectionException(401)

    coordinator.update_method = coordinator._async_update_with_retry(
        mock_update_auth_error
    )

    await coordinator.async_refresh()

    assert call_count == 1
    assert coordinator.last_update_success is False
    assert "401" in str(coordinator.last_exception)


async def test_coordinator_timeout_retry(coordinator, mock_device):
    """Test retry on timeout."""
    call_count = 0

    async def mock_update_timeout():
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            raise asyncio.TimeoutError()
        return None

    coordinator.update_method = coordinator._async_update_with_retry(
        mock_update_timeout
    )

    await coordinator.async_refresh()

    assert call_count == 2


# --- Write verification ---------------------------------------------------


def _pending_temperature(expected=55):
    from custom_components.ariston.coordinator import PendingWrite

    return PendingWrite(prop="temperature", expected=expected)


async def test_pending_write_cleared_when_device_matches(coordinator, mock_device):
    """A write that shows up in the next poll is cleared without retrying."""
    mock_device.water_heater_target_temperature = 55
    mock_device.async_set_water_heater_temperature = AsyncMock()
    coordinator.pending_writes["temperature"] = _pending_temperature()

    await coordinator._async_check_pending_writes()

    assert coordinator.pending_writes == {}
    mock_device.async_set_water_heater_temperature.assert_not_awaited()


async def test_pending_write_retried_on_mismatch(coordinator, mock_device):
    """A write ignored by the cloud is sent again on the next poll."""
    mock_device.water_heater_target_temperature = 50
    mock_device.async_set_water_heater_temperature = AsyncMock()
    pending = _pending_temperature()
    coordinator.pending_writes["temperature"] = pending

    await coordinator._async_check_pending_writes()

    mock_device.async_set_water_heater_temperature.assert_awaited_once_with(55)
    assert pending.tries == 1
    assert coordinator.pending_writes["temperature"] is pending


async def test_pending_write_gives_up_after_max_tries(coordinator, mock_device):
    """Verification must never loop forever."""
    mock_device.water_heater_target_temperature = 50
    mock_device.async_set_water_heater_temperature = AsyncMock()
    pending = _pending_temperature()
    pending.tries = pending.max_tries
    coordinator.pending_writes["temperature"] = pending

    await coordinator._async_check_pending_writes()

    assert coordinator.pending_writes == {}
    mock_device.async_set_water_heater_temperature.assert_not_awaited()


async def test_pending_write_retry_failure_is_non_fatal(coordinator, mock_device):
    """A failing retry keeps polling alive and schedules another attempt."""
    mock_device.water_heater_target_temperature = 50
    mock_device.async_set_water_heater_temperature = AsyncMock(
        side_effect=RuntimeError("cloud down")
    )
    pending = _pending_temperature()
    coordinator.pending_writes["temperature"] = pending

    await coordinator._async_check_pending_writes()

    assert coordinator.pending_writes["temperature"] is pending
    assert pending.tries == 1


async def test_pending_write_unknown_prop_is_dropped(coordinator, mock_device):
    """An unverifiable prop cannot be checked, so it is discarded."""
    from custom_components.ariston.coordinator import PendingWrite

    coordinator.pending_writes["unknown"] = PendingWrite(
        prop="unknown", expected="whatever"
    )

    await coordinator._async_check_pending_writes()

    assert coordinator.pending_writes == {}


# --- Plant settings refresh ----------------------------------------------


async def test_settings_refreshed_on_first_poll(coordinator, mock_device):
    """Velis devices get their plant settings loaded."""
    mock_device.async_update_settings = AsyncMock()

    await coordinator._async_refresh_settings()

    mock_device.async_update_settings.assert_awaited_once()
    assert coordinator._last_settings_refresh is not None


async def test_settings_refresh_is_rate_limited(coordinator, mock_device):
    """Settings are not re-fetched on every poll."""
    from custom_components.ariston.coordinator import SETTINGS_REFRESH_INTERVAL

    mock_device.async_update_settings = AsyncMock()

    await coordinator._async_refresh_settings()
    await coordinator._async_refresh_settings()
    mock_device.async_update_settings.assert_awaited_once()

    coordinator._last_settings_refresh = (
        datetime.now(UTC) - SETTINGS_REFRESH_INTERVAL - timedelta(seconds=1)
    )
    await coordinator._async_refresh_settings()
    assert mock_device.async_update_settings.await_count == 2


async def test_settings_refresh_failure_is_non_fatal(coordinator, mock_device):
    """A broken settings endpoint must not break the state poll."""
    mock_device.async_update_settings = AsyncMock(side_effect=RuntimeError("boom"))

    await coordinator._async_refresh_settings()

    assert coordinator.last_update_success is not False


async def test_secondary_coordinator_skips_settings_and_writes(mock_hass, mock_device):
    """Only the main coordinator refreshes settings and verifies writes."""
    mock_device.async_update_settings = AsyncMock()

    async def mock_update():
        pass

    coordinator = DeviceDataUpdateCoordinator(
        hass=mock_hass,
        device=mock_device,
        scan_interval_seconds=300,
        coordinator_name="energy_coordinator",
        async_update_state=mock_update,
    )
    coordinator.pending_writes["temperature"] = _pending_temperature()

    await coordinator._async_update_and_verify()

    mock_device.async_update_settings.assert_not_awaited()
    assert coordinator.pending_writes


def _pending_power(expected=False):
    from custom_components.ariston.coordinator import PendingWrite

    return PendingWrite(prop="power", expected=expected)


async def test_pending_power_write_cleared_when_device_matches(
    coordinator, mock_device
):
    """A power change already applied by the cloud is not retried."""
    mock_device.water_heater_power_value = False
    mock_device.async_set_power = AsyncMock()
    coordinator.pending_writes["power"] = _pending_power(False)

    await coordinator._async_check_pending_writes()

    assert coordinator.pending_writes == {}
    mock_device.async_set_power.assert_not_awaited()


async def test_pending_power_write_retried_on_mismatch(coordinator, mock_device):
    """A power change ignored by the cloud is sent again."""
    mock_device.water_heater_power_value = True
    mock_device.async_set_power = AsyncMock()
    pending = _pending_power(False)
    coordinator.pending_writes["power"] = pending

    await coordinator._async_check_pending_writes()

    mock_device.async_set_power.assert_awaited_once_with(False)
    assert pending.tries == 1
