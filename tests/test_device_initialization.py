"""Test device initialization for the Gree Versati integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gree_versati.client import GreeVersatiClient
from custom_components.gree_versati.protocol import GreeBindError


@pytest.mark.asyncio
async def test_device_initialization_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
):
    """Test that device initialization succeeds with proper parameters."""
    # Create a mock device that reports negotiated credentials
    mock_device = MagicMock()
    mock_device.bind = AsyncMock(return_value="negotiated_key")
    mock_device.key = "negotiated_key"
    mock_device.cipher_type = "ecb"

    # Patch the AwhpDevice and DeviceInfo classes
    with (
        patch(
            "custom_components.gree_versati.client.AwhpDevice",
            return_value=mock_device,
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

        # Bind is a no-op/negotiation without arguments now; the stored
        # key and cipher live on the device object itself
        mock_device.bind.assert_awaited_once_with()

        # The client reflects what the device negotiated so the config
        # entry can persist it
        assert client.key == "negotiated_key"
        assert client.cipher_type == "ecb"


@pytest.mark.asyncio
async def test_device_initialization_bind_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
):
    """Test that device initialization surfaces bind failures."""
    # Create a mock device whose bind fails
    mock_device = MagicMock()
    mock_device.bind = AsyncMock(side_effect=GreeBindError("no answer"))

    # Patch the AwhpDevice and DeviceInfo classes
    with (
        patch(
            "custom_components.gree_versati.client.AwhpDevice",
            return_value=mock_device,
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

        # Initialize the device - this should raise a ConnectionError
        with pytest.raises(ConnectionError, match="Binding failed: no answer"):
            await client.initialize()


@pytest.mark.asyncio
async def test_init_setup_entry_retries_on_bind_failure(hass: HomeAssistant):
    """Setup raises ConfigEntryNotReady on bind failure so HA retries."""
    entry_data = {
        "ip": "192.168.1.100",
        "port": 7000,
        "name": "Test Gree Versati",
        "mac": "AA:BB:CC:DD:EE:FF",
        "key": "test_key",
    }

    # Create a real client but mock the device
    mock_device = MagicMock()
    mock_device.bind = AsyncMock(side_effect=GreeBindError("no answer"))

    # Patch the necessary classes
    with (
        patch(
            "custom_components.gree_versati.client.AwhpDevice",
            return_value=mock_device,
        ),
        patch("custom_components.gree_versati.client.DeviceInfo"),
        patch.object(hass, "async_add_executor_job", new_callable=AsyncMock),
    ):
        # Import the setup_entry function
        from custom_components.gree_versati import async_setup_entry

        # Create a proper ConfigEntry mock
        entry = MockConfigEntry(
            domain="gree_versati",
            data=entry_data,
            entry_id="test",
        )

        # Setup must signal HA to retry rather than fail permanently
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)

        mock_device.bind.assert_awaited_once_with()
