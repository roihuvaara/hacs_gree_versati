"""Test Gree Versati sensor."""
from unittest.mock import patch, MagicMock

from homeassistant.const import (
    UnitOfTemperature,
    STATE_UNAVAILABLE,
)

from custom_components.gree_versati.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_sensors(hass, mock_config_entry):
    """Test the creation and values of the sensors."""
    
    # Mock API client with some sensor values
    mock_client = MagicMock()
    mock_client.get_temperature.return_value = 22.5
    mock_client.get_water_temperature.return_value = 45.0
    mock_client.is_connected.return_value = True
    
    with patch("custom_components.gree_versati.client.GreeVersatiClient", return_value=mock_client):
        # Initialize the integration
        mock_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Check that sensors have correct states
        state = hass.states.get("sensor.test_gree_versati_temperature")
        assert state
        assert state.state == "22.5"
        assert state.attributes.get("unit_of_measurement") == UnitOfTemperature.CELSIUS
        
        state = hass.states.get("sensor.test_gree_versati_water_temperature")
        assert state
        assert state.state == "45.0"
        assert state.attributes.get("unit_of_measurement") == UnitOfTemperature.CELSIUS
        
        # Test disconnection
        mock_client.is_connected.return_value = False
        mock_client.get_temperature.return_value = None
        
        # Trigger an update
        async_update = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"].async_update
        await async_update()
        await hass.async_block_till_done()
        
        # Check that sensors become unavailable
        state = hass.states.get("sensor.test_gree_versati_temperature")
        assert state
        assert state.state == STATE_UNAVAILABLE 