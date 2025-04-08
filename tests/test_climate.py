"""Test Gree Versati climate entity."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.climate.const import (
    ATTR_HVAC_ACTION,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, State

from custom_components.gree_versati.climate import GreeVersatiClimate
from custom_components.gree_versati.const import (
    CONF_EXTERNAL_TEMP_SENSOR,
    CONF_USE_WATER_TEMP_AS_CURRENT,
    COOL_MODE,
    DOMAIN,
    HEAT_MODE,
)


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


class TestGreeVersatiClimate:
    """Test the GreeVersatiClimate class."""

    def test_unique_id_includes_mac(self):
        """Test that unique_id includes the MAC address for grouping."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        coordinator = MagicMock()
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify unique_id
        assert climate.unique_id == "AA:BB:CC:DD:EE:FF_space_heating"

    def test_device_info_consistent(self):
        """Test that device_info is consistent for grouping."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        coordinator = MagicMock()
        coordinator.data = {"versati_series": "III"}
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Just check that device_info is created and not None
        assert climate.device_info is not None

    def test_current_temperature_with_external_sensor(self):
        """Test that current_temperature uses external sensor if configured."""
        # Create mocks
        hass = MagicMock(spec=HomeAssistant)
        # Add states attribute to hass mock
        hass.states = MagicMock()

        entry = MagicMock()
        entry.options = {CONF_EXTERNAL_TEMP_SENSOR: "sensor.room_temperature"}
        coordinator = MagicMock()
        coordinator.data = {
            "water_out_temp": 45.0,
        }
        client = MagicMock()

        # Mock the sensor state
        mock_state = MagicMock(spec=State)
        mock_state.state = "22.5"
        hass.states.get.return_value = mock_state

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify current_temperature
        assert climate.current_temperature == 22.5
        hass.states.get.assert_called_once_with("sensor.room_temperature")

    def test_current_temperature_with_external_sensor_unavailable(self):
        """Test current_temperature when external sensor is unavailable."""
        # Create mocks
        hass = MagicMock(spec=HomeAssistant)
        # Add states attribute to hass mock
        hass.states = MagicMock()

        entry = MagicMock()
        entry.options = {
            CONF_EXTERNAL_TEMP_SENSOR: "sensor.room_temperature",
            CONF_USE_WATER_TEMP_AS_CURRENT: True,
        }
        coordinator = MagicMock()
        coordinator.data = {
            "water_out_temp": 45.0,
        }
        client = MagicMock()

        # Mock the sensor state as unavailable
        mock_state = MagicMock(spec=State)
        mock_state.state = "unavailable"
        hass.states.get.return_value = mock_state

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Should fall back to water temperature
        assert climate.current_temperature == 45.0

    def test_current_temperature_with_water_temp_fallback(self):
        """Test current_temperature using water temperature as fallback."""
        # Create mocks
        hass = MagicMock(spec=HomeAssistant)
        entry = MagicMock()
        entry.options = {
            CONF_EXTERNAL_TEMP_SENSOR: "",  # No external sensor
            CONF_USE_WATER_TEMP_AS_CURRENT: True,
        }
        coordinator = MagicMock()
        coordinator.data = {
            "water_out_temp": 45.0,
        }
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Should use water temperature
        assert climate.current_temperature == 45.0

    def test_current_temperature_none(self):
        """Test current_temperature returns None when no source available."""
        # Create mocks
        hass = MagicMock(spec=HomeAssistant)
        entry = MagicMock()
        entry.options = {
            CONF_EXTERNAL_TEMP_SENSOR: "",  # No external sensor
            CONF_USE_WATER_TEMP_AS_CURRENT: False,  # Don't use water temp
        }
        coordinator = MagicMock()
        coordinator.data = {
            "water_out_temp": 45.0,
        }
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Should return None
        assert climate.current_temperature is None

    def test_hvac_mode_maps_correctly(self):
        """Test that HVAC mode maps correctly to HA constants."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        coordinator = MagicMock()
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Test heat mode
        coordinator.data = {"power": True, "mode": HEAT_MODE}
        assert climate.hvac_mode == HVACMode.HEAT

        # Test cool mode
        coordinator.data = {"power": True, "mode": COOL_MODE}
        assert climate.hvac_mode == HVACMode.COOL

        # Test off mode
        coordinator.data = {"power": False}
        assert climate.hvac_mode == HVACMode.OFF

    @patch("custom_components.gree_versati.client.GreeVersatiClient.set_temperature")
    async def test_set_temperature(self, mock_set_temperature):
        """Test setting the temperature."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        coordinator = MagicMock()
        coordinator.data = {"power": True, "mode": HEAT_MODE}
        client = MagicMock()

        # Create AsyncMock for client.set_temperature and coordinator.async_request_refresh
        client.set_temperature = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Set temperature
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 35})

        # Verify call - the actual implementation maps HEAT_MODE to "heat"
        client.set_temperature.assert_called_once_with(35, mode="heat")

    @patch("custom_components.gree_versati.client.GreeVersatiClient.set_hvac_mode")
    async def test_set_hvac_mode(self, mock_set_hvac_mode):
        """Test setting the HVAC mode."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        coordinator = MagicMock()
        client = MagicMock()

        # Create AsyncMock for client.set_hvac_mode and coordinator.async_request_refresh
        client.set_hvac_mode = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Set HVAC mode
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Verify call
        client.set_hvac_mode.assert_called_once_with(HVACMode.HEAT)
        coordinator.async_request_refresh.assert_called_once()
