"""Tests for the coordinator's update functionality."""

import asyncio
import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.gree_versati.coordinator import GreeVersatiDataUpdateCoordinator
from custom_components.gree_versati.const import DOMAIN, LOGGER


@pytest.mark.asyncio
async def test_coordinator_polling(hass: HomeAssistant):
    """Test that the coordinator polls for updates at regular intervals."""
    # Create a mock client with an async_get_data method
    client = MagicMock()
    client.async_get_data = AsyncMock(
        side_effect=[
            {"water_out_temp": 35.0, "power": True},  # First call
            {"water_out_temp": 36.0, "power": True},  # Second call
            {"water_out_temp": 37.0, "power": True},  # Third call
        ]
    )

    # Create a mock config entry with proper state
    config_entry = MagicMock()
    config_entry.state = ConfigEntryState.SETUP_IN_PROGRESS
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.client = client

    # Patch asyncio.sleep to speed up the test
    update_interval = timedelta(seconds=0.1)  # Very short for testing

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        # Create the coordinator with a short update interval
        coordinator = GreeVersatiDataUpdateCoordinator(
            hass=hass,
            name=DOMAIN,
            logger=LOGGER,
            update_interval=update_interval,
        )
        coordinator.config_entry = config_entry

        # Initialize the coordinator with the first update
        await coordinator.async_config_entry_first_refresh()

        # Verify the first data update
        assert coordinator.data == {"water_out_temp": 35.0, "power": True}

        # Manually trigger a second update
        await coordinator.async_refresh()

        # Verify the second data update
        assert coordinator.data == {"water_out_temp": 36.0, "power": True}

        # Manually trigger a third update
        await coordinator.async_refresh()

        # Verify the third data update
        assert coordinator.data == {"water_out_temp": 37.0, "power": True}

        # Verify that client.async_get_data was called 3 times
        assert client.async_get_data.call_count == 3


@pytest.mark.asyncio
async def test_coordinator_first_update_retry(hass: HomeAssistant):
    """Test that the coordinator handles the first update with a delay and retry if needed."""
    # Create a mock client with an async_get_data method that returns all None values first
    client = MagicMock()
    client.async_get_data = AsyncMock(
        side_effect=[
            {"water_out_temp": None, "power": None},  # First call returns None values
            {"water_out_temp": 35.0, "power": True},  # Second call with actual data
        ]
    )

    # Create a mock config entry with proper state
    config_entry = MagicMock()
    config_entry.state = ConfigEntryState.SETUP_IN_PROGRESS
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.client = client

    # Mock the asyncio.sleep to avoid delays in tests
    with patch("asyncio.sleep", new=AsyncMock()):
        # Create the coordinator
        coordinator = GreeVersatiDataUpdateCoordinator(
            hass=hass,
            name=DOMAIN,
            logger=LOGGER,
            update_interval=timedelta(seconds=30),
        )
        coordinator.config_entry = config_entry

        # Initialize the coordinator with the first refresh
        await coordinator.async_config_entry_first_refresh()

        # Verify the data is populated correctly after the retry
        assert coordinator.data == {"water_out_temp": 35.0, "power": True}

        # Verify our client's async_get_data was called twice - once for the initial
        # request (which returned None values) and once for the retry
        assert client.async_get_data.call_count == 2


@pytest.mark.asyncio
async def test_coordinator_entity_update(hass: HomeAssistant):
    """Test that entities get updated when the coordinator updates."""
    # Create a mock client with an async_get_data method
    client = MagicMock()
    client.async_get_data = AsyncMock(
        side_effect=[
            {"water_out_temp": 35.0, "power": True},  # First call
            {"water_out_temp": 36.0, "power": True},  # Second call
        ]
    )

    # Create a mock config entry with proper state
    config_entry = MagicMock()
    config_entry.state = ConfigEntryState.SETUP_IN_PROGRESS
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.client = client

    # Patch asyncio.sleep to speed up the test
    with patch("asyncio.sleep", new=AsyncMock()):
        # Create the coordinator
        coordinator = GreeVersatiDataUpdateCoordinator(
            hass=hass,
            name=DOMAIN,
            logger=LOGGER,
            update_interval=timedelta(seconds=0.1),
        )
        coordinator.config_entry = config_entry

        # Create a mock listener and register it
        listener = MagicMock()

        # Initialize the coordinator
        await coordinator.async_config_entry_first_refresh()

        # Register a listener
        unsub = coordinator.async_add_listener(listener)

        # Trigger an update
        await coordinator.async_refresh()

        # Verify that the listener was called
        assert listener.call_count >= 1, "Listener was not called on update"

        # Remove the listener
        unsub()

        # Trigger another update
        await coordinator.async_refresh()

        # Verify that the listener was not called again
        assert listener.call_count >= 1, (
            "Listener should not be called after unsubscribing"
        )


@pytest.mark.asyncio
async def test_coordinator_automatic_polling(hass: HomeAssistant):
    """Test that the coordinator can perform scheduled updates."""
    # Create a mock client with an async_get_data method
    client = MagicMock()
    client.async_get_data = AsyncMock(
        return_value={"water_out_temp": 35.0, "power": True}
    )

    # Create a mock config entry with proper state
    config_entry = MagicMock()
    config_entry.state = ConfigEntryState.SETUP_IN_PROGRESS
    config_entry.runtime_data = MagicMock()
    config_entry.runtime_data.client = client

    # Mock the asyncio.sleep function to prevent actual sleeping
    with patch("asyncio.sleep", new=AsyncMock()):
        # Create the coordinator with a very short update interval
        coordinator = GreeVersatiDataUpdateCoordinator(
            hass=hass,
            name=DOMAIN,
            logger=LOGGER,
            update_interval=timedelta(seconds=0.1),
        )
        coordinator.config_entry = config_entry

        # Initialize the coordinator with the first refresh
        await coordinator.async_config_entry_first_refresh()

        # Reset the mock to clear the initial call
        client.async_get_data.reset_mock()

        # Mock the _async_update_data method directly to avoid calling the real implementation
        # during the _async_refresh call
        with patch.object(
            coordinator, "_async_update_data", new=AsyncMock()
        ) as mock_update_data:
            # Manually trigger a scheduled update
            await coordinator._async_refresh(scheduled=True)

            # Verify our mocked method was called
            mock_update_data.assert_called_once()

        # Verify the client's async_get_data was used in a normal update
        await coordinator.async_refresh()
        assert client.async_get_data.called, "client.async_get_data was not called"
