"""Test the GreeVersatiSensor class."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorEntityDescription

from custom_components.gree_versati.sensor import (
    ENTITY_DESCRIPTIONS,
    GreeVersatiSensor,
    async_setup_entry,
)


class TestGreeVersatiSensor:
    """Test the GreeVersatiSensor class."""

    def test_sensor_initialization(self):
        """Test sensor initialization."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

        # Create entity description
        entity_description = SensorEntityDescription(
            key="test_sensor",
            name="Test Sensor",
            icon="mdi:test-icon",
        )

        # Create the sensor
        sensor = GreeVersatiSensor(coordinator, entity_description)

        # Verify the sensor was initialized correctly
        assert sensor.entity_description == entity_description
        assert sensor._attr_unique_id == "test_entry_id"
        assert sensor._client == coordinator.config_entry.runtime_data.client

    def test_native_value(self):
        """Test native_value property."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"body": "test_value"}

        # Create entity description
        entity_description = SensorEntityDescription(
            key="test_sensor",
            name="Test Sensor",
        )

        # Create the sensor
        sensor = GreeVersatiSensor(coordinator, entity_description)

        # Verify native value
        assert sensor.native_value == "test_value"

    def test_native_value_missing(self):
        """Test native_value property when body is missing."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {}  # No body key

        # Create entity description
        entity_description = SensorEntityDescription(
            key="test_sensor",
            name="Test Sensor",
        )

        # Create the sensor
        sensor = GreeVersatiSensor(coordinator, entity_description)

        # Verify native value is None when body is missing
        assert sensor.native_value is None

    @pytest.mark.asyncio
    async def test_async_setup_entry(self):
        """Test the async_setup_entry function."""
        # Create mocks
        hass = MagicMock()
        entry = MagicMock()
        entry.runtime_data.coordinator = MagicMock()
        async_add_entities = MagicMock()

        # Call the setup function
        await async_setup_entry(hass, entry, async_add_entities)

        # Verify async_add_entities was called with the correct entities
        async_add_entities.assert_called_once()

        # Get the entities that were passed to async_add_entities
        entities = async_add_entities.call_args[0][0]

        # Verify the correct number of entities were created
        assert len(list(entities)) == len(ENTITY_DESCRIPTIONS)

        # Verify each entity is a GreeVersatiSensor
        for entity in entities:
            assert isinstance(entity, GreeVersatiSensor)
