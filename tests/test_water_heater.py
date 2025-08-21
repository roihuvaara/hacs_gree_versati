"""Test the GreeVersatiWaterHeater class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.water_heater import WaterHeaterEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from custom_components.gree_versati.water_heater import (
    OPERATION_LIST,
    GreeVersatiWaterHeater,
    async_setup_entry,
)


class TestGreeVersatiWaterHeater:
    """Test the GreeVersatiWaterHeater class."""

    def test_water_heater_initialization(self):
        """Test water heater initialization."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client and wire it via runtime_data as the entity expects
        client = MagicMock()
        client.mac = "AA:BB:CC:DD:EE:FF"
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify the water heater entity was initialized correctly
        assert water_heater._attr_temperature_unit == UnitOfTemperature.CELSIUS
        assert water_heater._attr_operation_list == OPERATION_LIST
        assert water_heater._attr_has_entity_name is True
        assert (
            not hasattr(water_heater, "_attr_name") or water_heater._attr_name is None
        )
        assert water_heater._attr_supported_features == (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )
        assert water_heater._client == client
        assert water_heater._attr_unique_id == "test_entry_id_water_heater"

    def test_translation_key(self):
        """Test translation_key property."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify translation key
        assert water_heater.translation_key == "water_heater"

    def test_current_temperature(self):
        """Test current_temperature property."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.data = {"hot_water_temp": 50.0}

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify current temperature
        assert water_heater.current_temperature == 50.0

    def test_target_temperature(self):
        """Test target_temperature property."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.data = {"hot_water_temp_set": 55.0}

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify target temperature
        assert water_heater.target_temperature == 55.0

    def test_current_operation_normal(self):
        """Test current_operation property in normal mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.data = {"fast_heat_water": False}

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify current operation
        assert water_heater.current_operation == "normal"

    def test_current_operation_performance(self):
        """Test current_operation property in performance mode."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.data = {"fast_heat_water": True}

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify current operation
        assert water_heater.current_operation == "performance"

    @pytest.mark.asyncio
    async def test_async_set_temperature(self):
        """Test async_set_temperature method."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.async_request_refresh = AsyncMock()

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        client.set_dhw_temperature = AsyncMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Call set_temperature
        await water_heater.async_set_temperature(**{ATTR_TEMPERATURE: 60.0})

        # Verify client.set_dhw_temperature was called with correct parameters
        client.set_dhw_temperature.assert_called_once_with(60.0)

        # Verify coordinator.async_request_refresh was called
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_temperature_no_temp(self):
        """Test async_set_temperature method with no temperature."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        client.set_dhw_temperature = AsyncMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Call set_temperature with no temperature
        await water_heater.async_set_temperature()

        # Verify client.set_dhw_temperature was not called
        client.set_dhw_temperature.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_operation_mode(self):
        """Test async_set_operation_mode method."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.async_request_refresh = AsyncMock()

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        client.set_dhw_mode = AsyncMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Call set_operation_mode
        await water_heater.async_set_operation_mode("performance")

        # Verify client.set_dhw_mode was called with correct parameters
        client.set_dhw_mode.assert_called_once_with("performance")

        # Verify coordinator.async_request_refresh was called
        coordinator.async_request_refresh.assert_called_once()

    def test_hvac_mode_on(self):
        """Test hvac_mode property when target temperature is set."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.data = {"hot_water_temp_set": 55.0}

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify HVAC mode
        assert water_heater.hvac_mode == "on"

    def test_hvac_mode_off(self):
        """Test hvac_mode property when target temperature is not set."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.data = {"hot_water_temp_set": None}

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify HVAC mode
        assert water_heater.hvac_mode == "off"

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode_on(self):
        """Test async_set_hvac_mode method with 'on' mode."""
        # Create a mock coordinator
        coordinator = MagicMock()

        # Create a mock client
        client = MagicMock()

        # Create the water heater entity
        with patch(
            "custom_components.gree_versati.water_heater.GreeVersatiWaterHeater.target_temperature",
            new_callable=MagicMock(return_value=None),
        ):
            # Wire runtime_data for the entity
            coordinator.config_entry.entry_id = "test_entry_id"
            runtime_data = MagicMock()
            runtime_data.client = client
            coordinator.config_entry.runtime_data = runtime_data

            water_heater = GreeVersatiWaterHeater(coordinator)
            water_heater.async_set_temperature = AsyncMock()

            # Call set_hvac_mode with 'on'
            await water_heater.async_set_hvac_mode("on")

            # Verify async_set_temperature was called with default temperature
            water_heater.async_set_temperature.assert_called_once_with(temperature=50.0)

    @pytest.mark.asyncio
    async def test_async_set_hvac_mode_off(self):
        """Test async_set_hvac_mode method with 'off' mode."""
        # Create a mock coordinator
        coordinator = MagicMock()

        # Create a mock client
        client = MagicMock()

        # Create the water heater entity
        with patch(
            "custom_components.gree_versati.water_heater.GreeVersatiWaterHeater.target_temperature",
            new_callable=MagicMock(return_value=55.0),
        ):
            # Wire runtime_data for the entity
            coordinator.config_entry.entry_id = "test_entry_id"
            runtime_data = MagicMock()
            runtime_data.client = client
            coordinator.config_entry.runtime_data = runtime_data

            water_heater = GreeVersatiWaterHeater(coordinator)
            water_heater.async_set_temperature = AsyncMock()

            # Call set_hvac_mode with 'off'
            await water_heater.async_set_hvac_mode("off")

            # Verify async_set_temperature was called with None
            water_heater.async_set_temperature.assert_called_once_with(temperature=None)

    def test_hvac_modes(self):
        """Test hvac_modes property."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify HVAC modes
        assert water_heater.hvac_modes == ["on", "off"]

    def test_min_temp(self):
        """Test min_temp property."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify min temperature
        assert water_heater.min_temp == 30.0

    def test_max_temp(self):
        """Test max_temp property."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"

        # Create a mock client and wire it via runtime_data
        client = MagicMock()
        runtime_data = MagicMock()
        runtime_data.client = client
        coordinator.config_entry.runtime_data = runtime_data

        # Create the water heater entity
        water_heater = GreeVersatiWaterHeater(coordinator)

        # Verify max temperature
        assert water_heater.max_temp == 80.0

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
                "test_entry_id": {"coordinator": coordinator, "client": client},
            },
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

            # Verify the entity is a GreeVersatiWaterHeater
            assert isinstance(entities[0], GreeVersatiWaterHeater)
