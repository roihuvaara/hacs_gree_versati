"""Test the GreeVersatiClimate class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from custom_components.gree_versati.climate import GreeVersatiClimate, async_setup_entry


class TestGreeVersatiClimate:
    """Test the GreeVersatiClimate class."""

    def test_climate_initialization(self):
        """Test climate initialization."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"

        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify the climate entity was initialized correctly
        assert climate._attr_temperature_unit == UnitOfTemperature.CELSIUS
        assert climate._attr_target_temperature_step == 1
        assert (
            climate._attr_hvac_modes == []
        )  # No modes since mode control is in select entity
        assert climate._attr_has_entity_name is True
        assert climate._attr_name == "Space Heating"
        assert (
            climate._attr_supported_features == ClimateEntityFeature.TARGET_TEMPERATURE
        )
        assert climate._client == client
        assert climate._attr_unique_id == "AA:BB:CC:DD:EE:FF_climate"

    def test_translation_key(self):
        """Test translation_key property."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"

        # Create a mock coordinator
        coordinator = MagicMock()

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify translation key
        assert climate.translation_key == "climate"

    def test_current_temperature(self):
        """Test current_temperature property."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"water_out_temp": 45.5}

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify current temperature
        assert climate.current_temperature is None  # Default behavior with no options

    def test_target_temperature_heat_mode(self):
        """Test target_temperature property in heat mode."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "mode": "heat",
            "heat_temp_set": 50.0,
        }

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify target temperature
        assert climate.target_temperature == 50.0

    def test_target_temperature_cool_mode(self):
        """Test target_temperature property in cool mode."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "mode": "cool",
            "cool_temp_set": 22.0,
        }

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify target temperature
        assert climate.target_temperature == 22.0

    def test_target_temperature_off_mode(self):
        """Test target_temperature property in off mode."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"mode": "off"}

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify target temperature is None when off
        assert climate.target_temperature is None

    def test_hvac_mode(self):
        """Test hvac_mode property always returns None."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": "heat",
        }

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Verify HVAC mode is always None
        assert climate.hvac_mode is None

    @pytest.mark.asyncio
    async def test_async_set_temperature(self):
        """Test async_set_temperature method."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"mode": "heat"}

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"
        client.set_temperature = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Call set_temperature
        await climate.async_set_temperature(temperature=50.0)

        # Verify client.set_temperature was called with correct parameters
        client.set_temperature.assert_called_once_with(50.0, mode="heat")

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode(self):
        """Test async_set_hvac_mode is a no-op."""
        # Create mock objects
        hass = MagicMock()
        entry = MagicMock()
        entry.title = "Test Device"
        entry.options = {}

        # Create a mock coordinator
        coordinator = MagicMock()

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(hass, entry, coordinator, client)

        # Call set_hvac_mode - should do nothing
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Verify no client methods were called
        assert not client.method_calls

    @pytest.mark.asyncio
    async def test_async_setup_entry(self):
        """Test the async_setup_entry function."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        async_add_entities = MagicMock()

        # Create coordinator and client mocks
        coordinator = MagicMock()
        client = MagicMock()

        # Setup hass.data with the correct structure
        hass.data = {
            "gree_versati": {
                "test_entry_id": {"coordinator": coordinator, "client": client}
            }
        }

        # Create a class-like object with coordinator and client attributes
        data_obj = MagicMock()
        data_obj.coordinator = coordinator
        data_obj.client = client

        # Patch the dictionary access to return our object
        with patch.dict(hass.data["gree_versati"], {"test_entry_id": data_obj}):
            # Call the setup function
            await async_setup_entry(hass, entry, async_add_entities)

            # Verify async_add_entities was called with the correct entities
            async_add_entities.assert_called_once()

            # Get the entities that were passed to async_add_entities
            entities = async_add_entities.call_args[0][0]

            # Verify the correct number of entities were created
            assert len(entities) == 1

            # Verify the entity is a GreeVersatiClimate
            assert isinstance(entities[0], GreeVersatiClimate)
