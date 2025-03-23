"""Test the GreeVersatiEntity class."""

from unittest.mock import MagicMock

from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.gree_versati.const import ATTRIBUTION, DOMAIN
from custom_components.gree_versati.entity import GreeVersatiEntity


class TestGreeVersatiEntity:
    """Test the GreeVersatiEntity class."""

    def test_entity_initialization(self):
        """Test entity initialization."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

        # Create the entity
        entity = GreeVersatiEntity(coordinator)

        # Verify the entity was initialized correctly
        assert entity._attr_attribution == ATTRIBUTION
        assert entity._attr_has_entity_name is True
        assert entity._attr_unique_id == "test_entry_id"
        assert entity._client == coordinator.config_entry.runtime_data.client

    def test_device_info_with_series(self):
        """Test device_info property with versati series."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.title = "Test Device"
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"
        coordinator.data = {"versati_series": "III"}

        # Create the entity
        entity = GreeVersatiEntity(coordinator)

        # Get device info
        device_info = entity.device_info

        # Create expected device info
        expected_device_info = DeviceInfo(
            identifiers={(DOMAIN, "AA:BB:CC:DD:EE:FF")},
            name="Test Device",
            manufacturer="Gree",
            model="Versati (III)",
        )

        # Verify device info
        assert device_info == expected_device_info

    def test_device_info_without_series(self):
        """Test device_info property without versati series."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.title = "Test Device"
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"
        coordinator.data = {}  # No versati_series

        # Create the entity
        entity = GreeVersatiEntity(coordinator)

        # Get device info
        device_info = entity.device_info

        # Create expected device info
        expected_device_info = DeviceInfo(
            identifiers={(DOMAIN, "AA:BB:CC:DD:EE:FF")},
            name="Test Device",
            manufacturer="Gree",
            model="Versati",
        )

        # Verify device info
        assert device_info == expected_device_info
