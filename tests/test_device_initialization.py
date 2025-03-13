"""Test device initialization for the Gree Versati integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gree_versati.client import GreeVersatiClient


@pytest.mark.asyncio
async def test_device_initialization_success(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test that device initialization succeeds with proper parameters."""
    # Create a mock device
    mock_device = MagicMock()
    mock_device.bind = AsyncMock(return_value=None)

    # Patch the AwhpDevice and DeviceInfo classes
    with (
        patch(
            "custom_components.gree_versati.client.AwhpDevice", return_value=mock_device
        ),
        patch("custom_components.gree_versati.client.DeviceInfo"),
    ):
        # Create a client with the correct parameters
        client = GreeVersatiClient(
            ip=mock_config_entry.data["ip"],
            port=mock_config_entry.data["port"],
            mac=mock_config_entry.data["mac"],
            key=mock_config_entry.data["key"],
        )

        # Initialize the device
        await client.initialize()

        # Verify the device was initialized correctly
        assert client.device is not None
        assert client.device == mock_device

        # Verify bind was called with the correct key
        client.device.bind.assert_called_once_with(key=mock_config_entry.data["key"])


@pytest.mark.asyncio
async def test_device_initialization_failure_missing_cipher(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test that device initialization fails when cipher is missing but key is provided."""
    # Create a mock device
    mock_device = MagicMock()
    # Simulate the error we're seeing in the logs
    mock_device.bind = AsyncMock(
        side_effect=Exception("cipher must be provided when key is provided")
    )

    # Patch the AwhpDevice and DeviceInfo classes
    with (
        patch(
            "custom_components.gree_versati.client.AwhpDevice", return_value=mock_device
        ),
        patch("custom_components.gree_versati.client.DeviceInfo"),
    ):
        # Create a client with the correct parameters
        client = GreeVersatiClient(
            ip=mock_config_entry.data["ip"],
            port=mock_config_entry.data["port"],
            mac=mock_config_entry.data["mac"],
            key=mock_config_entry.data["key"],
        )

        # Initialize the device - this should raise an exception
        with pytest.raises(Exception) as excinfo:
            await client.initialize()

        # Verify the exception message
        assert "Binding failed: cipher must be provided when key is provided" in str(
            excinfo.value
        )


@pytest.mark.asyncio
async def test_init_setup_entry_fails_with_missing_cipher(hass: HomeAssistant):
    """Test that the integration setup fails when cipher is required but not provided."""
    # Create a mock entry
    entry_data = {
        "ip": "192.168.1.100",
        "port": 7000,
        "name": "Test Gree Versati",
        "mac": "AA:BB:CC:DD:EE:FF",
        "key": "test_key",
    }

    # Create a real client but mock the device
    mock_device = MagicMock()
    mock_device.bind = AsyncMock(
        side_effect=Exception("cipher must be provided when key is provided")
    )

    # Patch the necessary classes
    with (
        patch(
            "custom_components.gree_versati.client.AwhpDevice", return_value=mock_device
        ),
        patch("custom_components.gree_versati.client.DeviceInfo"),
    ):
        # Import the setup_entry function
        from custom_components.gree_versati import async_setup_entry

        # Create a mock entry
        entry = MagicMock()
        entry.data = entry_data
        entry.entry_id = "test"

        # Call the setup entry function directly
        result = await async_setup_entry(hass, entry)

        # Verify the result is False, indicating setup failed
        assert result is False

        # Verify the device.bind method was called
        mock_device.bind.assert_called_once_with(key=entry_data["key"])
