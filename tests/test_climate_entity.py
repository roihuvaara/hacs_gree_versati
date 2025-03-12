"""Test the GreeVersatiClimate class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

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
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify the climate entity was initialized correctly
        assert climate._attr_temperature_unit == UnitOfTemperature.CELSIUS
        assert climate._attr_target_temperature_step == 1
        assert climate._attr_hvac_modes == [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
        assert climate._attr_supported_features == (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )
        assert climate._client == client
        assert climate._attr_unique_id == "gree_versati_AA:BB:CC:DD:EE:FF"

    def test_translation_key(self):
        """Test translation_key property."""
        # Create a mock coordinator
        coordinator = MagicMock()

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify translation key
        assert climate.translation_key == "climate"

    def test_current_temperature(self):
        """Test current_temperature property."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"water_out_temp": 45.5}

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify current temperature
        assert climate.current_temperature == 45.5

    def test_target_temperature_heat_mode(self):
        """Test target_temperature property in heat mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 4,  # Heat mode
            "heat_temp_set": 50.0,
        }

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify target temperature
        assert climate.target_temperature == 50.0

    def test_target_temperature_cool_mode(self):
        """Test target_temperature property in cool mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 1,  # Cool mode
            "cool_temp_set": 22.0,
        }

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify target temperature
        assert climate.target_temperature == 22.0

    def test_target_temperature_off_mode(self):
        """Test target_temperature property in off mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"power": False}

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify target temperature is None when off
        assert climate.target_temperature is None

    def test_hvac_mode_off(self):
        """Test hvac_mode property when power is off."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"power": False}

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify HVAC mode
        assert climate.hvac_mode == HVACMode.OFF

    def test_hvac_mode_heat(self):
        """Test hvac_mode property in heat mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 4,  # Heat mode
        }

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify HVAC mode
        assert climate.hvac_mode == HVACMode.HEAT

    def test_hvac_mode_cool(self):
        """Test hvac_mode property in cool mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 1,  # Cool mode
        }

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify HVAC mode
        assert climate.hvac_mode == HVACMode.COOL

    def test_hvac_mode_unknown(self):
        """Test hvac_mode property with unknown mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 99,  # Unknown mode
        }

        # Create a mock client
        client = MagicMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Verify HVAC mode defaults to OFF for unknown modes
        assert climate.hvac_mode == HVACMode.OFF

    @pytest.mark.asyncio
    async def test_async_set_temperature_heat(self):
        """Test async_set_temperature method in heat mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 4,  # Heat mode
        }

        # Create a mock client with AsyncMock for set_temperature
        client = MagicMock()
        client.set_temperature = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Call set_temperature
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 50.0})

        # Verify client.set_temperature was called with correct parameters
        client.set_temperature.assert_called_once_with(50.0, mode="heat")

    @pytest.mark.asyncio
    async def test_async_set_temperature_cool(self):
        """Test async_set_temperature method in cool mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {
            "power": True,
            "mode": 1,  # Cool mode
        }

        # Create a mock client with AsyncMock for set_temperature
        client = MagicMock()
        client.set_temperature = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Call set_temperature
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 22.0})

        # Verify client.set_temperature was called with correct parameters
        client.set_temperature.assert_called_once_with(22.0, mode="cool")

    @pytest.mark.asyncio
    async def test_async_set_temperature_no_temp(self):
        """Test async_set_temperature method with no temperature."""
        # Create a mock coordinator
        coordinator = MagicMock()

        # Create a mock client
        client = MagicMock()
        client.set_temperature = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Call set_temperature with no temperature
        await climate.async_set_temperature(**{})

        # Verify client.set_temperature was not called
        client.set_temperature.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode(self):
        """Test async_set_hvac_mode method."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.async_request_refresh = AsyncMock()

        # Create a mock client
        client = MagicMock()
        client.set_hvac_mode = AsyncMock()

        # Create the climate entity
        climate = GreeVersatiClimate(coordinator, client)

        # Call set_hvac_mode
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Verify client.set_hvac_mode was called with correct parameters
        client.set_hvac_mode.assert_called_once_with(HVACMode.HEAT)

        # Verify coordinator.async_request_refresh was called
        coordinator.async_request_refresh.assert_called_once()

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
