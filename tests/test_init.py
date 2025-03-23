"""Test gree_versati integration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gree_versati.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test successful setup of config entry."""
    # Mock the API client to avoid actual network calls
    with patch(
        "custom_components.gree_versati.client.GreeVersatiClient",
    ) as mock_client_class:
        # Configure the mock to return success
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.initialize.return_value = None

        # Add the config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Setup the entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify the integration was set up correctly
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_setup_entry_fails_cannot_connect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
):
    """Test failed setup when connection fails."""
    with patch(
        "custom_components.gree_versati.client.GreeVersatiClient",
    ) as mock_client_class:
        # Configure the mock to return failure
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        mock_client_instance.initialize.side_effect = Exception("Cannot connect")

        # Add the config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Setup should fail
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        assert not result
