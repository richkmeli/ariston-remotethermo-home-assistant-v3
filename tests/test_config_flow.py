"""Tests for Ariston config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ariston.ariston_api import ConnectionException

from custom_components.ariston.config_flow import (
    AristonConfigFlow,
    STEP_USER_DATA_SCHEMA,
)


@pytest.fixture
def config_flow():
    """Create a config flow instance."""
    flow = AristonConfigFlow()
    flow.hass = MagicMock()
    flow.hass.config_entries = MagicMock()
    # The flow manager normally initializes the context before running a flow.
    flow.context = {"source": "user"}
    return flow


def test_step_user_data_schema():
    """Test the user step data schema."""
    schema = STEP_USER_DATA_SCHEMA
    assert "username" in schema.schema
    assert "password" in schema.schema
    assert "api_url_setting" in schema.schema
    assert "api_user_agent" in schema.schema


async def test_async_step_user_success(config_flow):
    """Test successful user step."""
    user_input = {
        "username": "test@example.com",
        "password": "password123",
        "api_url_setting": "https://api.ariston.com",
        "api_user_agent": "TestAgent/1.0",
    }

    with patch("custom_components.ariston.config_flow.Ariston") as mock_ariston_class:
        mock_ariston = AsyncMock()
        mock_ariston_class.return_value = mock_ariston
        mock_ariston.async_connect = AsyncMock(return_value=True)
        mock_ariston.async_discover = AsyncMock(
            return_value=[{"gw": "gateway123", "name": "Test Device", "sn": "SN123"}]
        )

        result = await config_flow.async_step_user(user_input)

        assert result["type"] == "create_entry"
        assert result["title"] == "Test Device"
        assert result["data"]["username"] == "test@example.com"


async def test_async_step_user_invalid_auth(config_flow):
    """Test user step with invalid auth."""
    user_input = {
        "username": "test@example.com",
        "password": "wrongpassword",
        "api_url_setting": "https://api.ariston.com",
        "api_user_agent": "TestAgent/1.0",
    }

    with patch("custom_components.ariston.config_flow.Ariston") as mock_ariston_class:
        mock_ariston = AsyncMock()
        mock_ariston_class.return_value = mock_ariston
        mock_ariston.async_connect = AsyncMock(return_value=False)

        result = await config_flow.async_step_user(user_input)

        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_auth"


async def test_async_step_user_connection_error(config_flow):
    """Test user step with connection error."""
    user_input = {
        "username": "test@example.com",
        "password": "password123",
        "api_url_setting": "https://api.ariston.com",
        "api_user_agent": "TestAgent/1.0",
    }

    with patch("custom_components.ariston.config_flow.Ariston") as mock_ariston_class:
        mock_ariston = AsyncMock()
        mock_ariston_class.return_value = mock_ariston
        mock_ariston.async_connect = AsyncMock(
            side_effect=ConnectionException("Connection failed")
        )

        result = await config_flow.async_step_user(user_input)

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"


async def test_async_step_user_no_devices(config_flow):
    """Test user step when no devices found."""
    user_input = {
        "username": "test@example.com",
        "password": "password123",
        "api_url_setting": "https://api.ariston.com",
        "api_user_agent": "TestAgent/1.0",
    }

    with patch("custom_components.ariston.config_flow.Ariston") as mock_ariston_class:
        mock_ariston = AsyncMock()
        mock_ariston_class.return_value = mock_ariston
        mock_ariston.async_connect = AsyncMock(return_value=True)
        mock_ariston.async_discover = AsyncMock(return_value=[])

        result = await config_flow.async_step_user(user_input)

        assert result["type"] == "form"
        assert result["errors"]["base"] == "no device found"


async def test_async_step_user_multiple_devices(config_flow):
    """Test user step with multiple devices."""
    user_input = {
        "username": "test@example.com",
        "password": "password123",
        "api_url_setting": "https://api.ariston.com",
        "api_user_agent": "TestAgent/1.0",
    }

    with patch("custom_components.ariston.config_flow.Ariston") as mock_ariston_class:
        mock_ariston = AsyncMock()
        mock_ariston_class.return_value = mock_ariston
        mock_ariston.async_connect = AsyncMock(return_value=True)
        mock_ariston.async_discover = AsyncMock(
            return_value=[
                {"gw": "gateway1", "name": "Device 1", "sn": "SN1"},
                {"gw": "gateway2", "name": "Device 2", "sn": "SN2"},
            ]
        )

        result = await config_flow.async_step_user(user_input)

        assert result["type"] == "form"
        assert result["step_id"] == "select"
        assert "select_device" in result["data_schema"].schema
