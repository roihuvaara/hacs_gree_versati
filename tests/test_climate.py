"""Test Gree Versati climate entity."""

from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from homeassistant.components.climate.const import (
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
)
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.gree_versati.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_climate_entity(hass, mock_config_entry):
    """Test the climate entity."""

    # Mock API client with climate data
    mock_client = MagicMock()
    mock_client.get_temperature.return_value = 22.5
    mock_client.get_target_temperature.return_value = 24.0
    mock_client.get_hvac_mode.return_value = "heat"
    mock_client.get_hvac_action.return_value = "heating"
    mock_client.is_connected.return_value = True
    mock_client.set_target_temperature = AsyncMock()
    mock_client.set_hvac_mode = AsyncMock()

    with patch(
        "custom_components.gree_versati.client.GreeVersatiClient",
        return_value=mock_client,
    ):
        # Initialize the integration
        mock_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that climate entity has correct state and attributes
        state = hass.states.get("climate.test_gree_versati")
        assert state
        assert state.state == "heat"
        assert state.attributes.get("current_temperature") == 22.5
        assert state.attributes.get("temperature") == 24.0
        assert state.attributes.get(ATTR_HVAC_ACTION) == "heating"

        # Test setting temperature
        await hass.services.async_call(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.test_gree_versati",
                ATTR_TEMPERATURE: 25.0,
            },
            blocking=True,
        )

        # Verify API call was made
        mock_client.set_target_temperature.assert_called_once_with(25.0)

        # Test setting HVAC mode
        await hass.services.async_call(
            "climate",
            "set_hvac_mode",
            {
                "entity_id": "climate.test_gree_versati",
                "hvac_mode": "cool",
            },
            blocking=True,
        )

        # Verify API call was made
        mock_client.set_hvac_mode.assert_called_once_with("cool")
