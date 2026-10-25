"""Tests for DeviceDataUpdateCoordinator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ariston.ariston_api import ConnectionException
from ariston.base_device import AristonBaseDevice

from custom_components.ariston.coordinator import DeviceDataUpdateCoordinator


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.loop = asyncio.get_event_loop()
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

    coordinator.update_method = coordinator._async_update_with_retry(mock_update_rate_limited)

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

    coordinator.update_method = coordinator._async_update_with_retry(mock_update_server_error)

    # Should succeed on third attempt
    await coordinator.async_refresh()

    assert call_count == 3


async def test_coordinator_max_retries_exceeded(coordinator, mock_device):
    """Test UpdateFailed raised after max retries."""
    async def mock_update_always_fails():
        raise ConnectionException(500)

    coordinator.update_method = coordinator._async_update_with_retry(mock_update_always_fails)

    from homeassistant.helpers.update_coordinator import UpdateFailed

    with pytest.raises(UpdateFailed):
        await coordinator.async_refresh()


async def test_coordinator_non_retryable_error(coordinator, mock_device):
    """Test non-retryable errors are raised immediately."""
    async def mock_update_auth_error():
        raise ConnectionException(401)

    coordinator.update_method = coordinator._async_update_with_retry(mock_update_auth_error)

    from homeassistant.helpers.update_coordinator import UpdateFailed

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator.async_refresh()

    assert "401" in str(exc_info.value)


async def test_coordinator_timeout_retry(coordinator, mock_device):
    """Test retry on timeout."""
    call_count = 0

    async def mock_update_timeout():
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            raise asyncio.TimeoutError()
        return None

    coordinator.update_method = coordinator._async_update_with_retry(mock_update_timeout)

    await coordinator.async_refresh()

    assert call_count == 2