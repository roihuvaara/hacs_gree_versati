"""Test the GreeVersatiBinarySensor class."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.gree_versati.binary_sensor import (
    ENTITY_DESCRIPTIONS,
    GreeVersatiBinarySensor,
    async_setup_entry,
)
from custom_components.gree_versati.const import DOMAIN


class TestGreeVersatiBinarySensor:
    """Test the GreeVersatiBinarySensor class."""

    def test_binary_sensor_initialization(self):
        """Test binary sensor initialization."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

        # Create entity description
        entity_description = BinarySensorEntityDescription(
            key="test_binary_sensor",
            name="Test Binary Sensor",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        )

        # Create the binary sensor
        binary_sensor = GreeVersatiBinarySensor(coordinator, entity_description)

        # Verify the binary sensor was initialized correctly
        assert binary_sensor.entity_description == entity_description
        assert binary_sensor._attr_unique_id == "test_entry_id"
        assert binary_sensor.coordinator == coordinator

    def test_is_on_true(self):
        """Test is_on property when title is 'foo'."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"title": "foo"}

        # Create entity description
        entity_description = BinarySensorEntityDescription(
            key="test_binary_sensor",
            name="Test Binary Sensor",
        )

        # Create the binary sensor
        binary_sensor = GreeVersatiBinarySensor(coordinator, entity_description)

        # Verify is_on is True when title is 'foo'
        assert binary_sensor.is_on is True

    def test_is_on_false(self):
        """Test is_on property when title is not 'foo'."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"title": "bar"}

        # Create entity description
        entity_description = BinarySensorEntityDescription(
            key="test_binary_sensor",
            name="Test Binary Sensor",
        )

        # Create the binary sensor
        binary_sensor = GreeVersatiBinarySensor(coordinator, entity_description)

        # Verify is_on is False when title is not 'foo'
        assert binary_sensor.is_on is False

    def test_is_on_missing_title(self):
        """Test is_on property when title is missing."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {}  # No title key

        # Create entity description
        entity_description = BinarySensorEntityDescription(
            key="test_binary_sensor",
            name="Test Binary Sensor",
        )

        # Create the binary sensor
        binary_sensor = GreeVersatiBinarySensor(coordinator, entity_description)

        # Verify is_on is False when title is missing
        assert binary_sensor.is_on is False

    def test_device_info_with_series(self):
        """Test device_info property with versati series."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"versati_series": "III"}
        coordinator.config_entry.title = "Test Device"
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

        # Create entity description
        entity_description = BinarySensorEntityDescription(
            key="test_binary_sensor",
            name="Test Binary Sensor",
        )

        # Create the binary sensor
        binary_sensor = GreeVersatiBinarySensor(coordinator, entity_description)

        # Verify device info
        device_info = binary_sensor.device_info
        expected_info = DeviceInfo(
            identifiers={(DOMAIN, "AA:BB:CC:DD:EE:FF")},
            name="Test Device",
            manufacturer="Gree",
            model="Versati (III)",
        )
        assert device_info == expected_info

    def test_device_info_without_series(self):
        """Test device_info property without versati series."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {}  # No versati_series
        coordinator.config_entry.title = "Test Device"
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

        # Create entity description
        entity_description = BinarySensorEntityDescription(
            key="test_binary_sensor",
            name="Test Binary Sensor",
        )

        # Create the binary sensor
        binary_sensor = GreeVersatiBinarySensor(coordinator, entity_description)

        # Verify device info
        device_info = binary_sensor.device_info
        expected_info = DeviceInfo(
            identifiers={(DOMAIN, "AA:BB:CC:DD:EE:FF")},
            name="Test Device",
            manufacturer="Gree",
            model="Versati",
        )
        assert device_info == expected_info

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

        # Verify each entity is a GreeVersatiBinarySensor
        for entity in entities:
            assert isinstance(entity, GreeVersatiBinarySensor)
