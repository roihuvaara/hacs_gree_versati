"""Tests for the device mode Select entity (TDD first)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_select_initialization_and_options():
    """Select should initialize with 6 modes in stable order."""
    from custom_components.gree_versati.select import GreeVersatiDeviceModeSelect

    # Create a mock coordinator and entry
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

    # Create the select
    select = GreeVersatiDeviceModeSelect(coordinator)

    # Verify unique_id and options
    assert select._attr_unique_id == "test_entry_id_device_mode"
    assert select.options == [
        "off",
        "cool",
        "heat",
        "hot_water",
        "cool_hot_water",
        "heat_hot_water",
    ]


@pytest.mark.asyncio
async def test_select_calls_client_on_choose():
    """Selecting a mode should call client.set_device_mode and refresh."""
    from custom_components.gree_versati.select import GreeVersatiDeviceModeSelect

    # Mock coordinator and client
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.set_device_mode = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()

    select = GreeVersatiDeviceModeSelect(coordinator)

    await select.async_select_option("hot_water")

    coordinator.config_entry.runtime_data.client.set_device_mode.assert_awaited_once_with(
        "hot_water"
    )
    # Expected state is published optimistically instead of polling
    coordinator.async_apply_optimistic_device_mode.assert_called_once_with("hot_water")


@pytest.mark.asyncio
async def test_async_setup_entry_adds_entity():
    """Platform setup should add the select entity."""
    from custom_components.gree_versati.select import (
        GreeVersatiDeviceModeSelect,
        async_setup_entry,
    )

    hass = MagicMock()
    entry = MagicMock()
    entry.runtime_data.coordinator = MagicMock()
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = list(async_add_entities.call_args[0][0])
    assert len(entities) == 1
    assert isinstance(entities[0], GreeVersatiDeviceModeSelect)
