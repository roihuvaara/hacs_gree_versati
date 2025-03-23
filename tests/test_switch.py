"""Test the GreeVersatiSwitch class."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.switch import SwitchEntityDescription

from custom_components.gree_versati.switch import (
    ENTITY_DESCRIPTIONS,
    GreeVersatiSwitch,
    async_setup_entry,
)


class TestGreeVersatiSwitch:
    """Test the GreeVersatiSwitch class."""

    def test_switch_initialization(self):
        """Test switch initialization."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

        # Create entity description
        entity_description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
            icon="mdi:test-icon",
        )

        # Create the switch
        switch = GreeVersatiSwitch(coordinator, entity_description)

        # Verify the switch was initialized correctly
        assert switch._attr_entity_description == entity_description
        assert switch._attr_unique_id == "test_entry_id"
        assert switch.coordinator == coordinator

    def test_is_on_true(self):
        """Test is_on property when title is 'foo'."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"title": "foo"}

        # Create entity description
        entity_description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
        )

        # Create the switch
        switch = GreeVersatiSwitch(coordinator, entity_description)

        # Verify is_on is True when title is 'foo'
        assert switch.is_on is True

    def test_is_on_false(self):
        """Test is_on property when title is not 'foo'."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {"title": "bar"}

        # Create entity description
        entity_description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
        )

        # Create the switch
        switch = GreeVersatiSwitch(coordinator, entity_description)

        # Verify is_on is False when title is not 'foo'
        assert switch.is_on is False

    def test_is_on_missing_title(self):
        """Test is_on property when title is missing."""
        # Create a mock coordinator with data
        coordinator = MagicMock()
        coordinator.data = {}  # No title key

        # Create entity description
        entity_description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
        )

        # Create the switch
        switch = GreeVersatiSwitch(coordinator, entity_description)

        # Verify is_on is False when title is missing
        assert switch.is_on is False

    @pytest.mark.asyncio
    async def test_async_turn_on(self):
        """Test async_turn_on method."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.runtime_data.client.async_set_title = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        # Create entity description
        entity_description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
        )

        # Create the switch
        switch = GreeVersatiSwitch(coordinator, entity_description)

        # Call turn_on
        await switch.async_turn_on()

        # Verify client.async_set_title was called with 'bar'
        coordinator.config_entry.runtime_data.client.async_set_title.assert_called_once_with(
            "bar"
        )

        # Verify coordinator.async_request_refresh was called
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off(self):
        """Test async_turn_off method."""
        # Create a mock coordinator
        coordinator = MagicMock()
        coordinator.config_entry.runtime_data.client.async_set_title = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        # Create entity description
        entity_description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
        )

        # Create the switch
        switch = GreeVersatiSwitch(coordinator, entity_description)

        # Call turn_off
        await switch.async_turn_off()

        # Verify client.async_set_title was called with 'foo'
        coordinator.config_entry.runtime_data.client.async_set_title.assert_called_once_with(
            "foo"
        )

        # Verify coordinator.async_request_refresh was called
        coordinator.async_request_refresh.assert_called_once()

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

        # Verify each entity is a GreeVersatiSwitch
        for entity in entities:
            assert isinstance(entity, GreeVersatiSwitch)
