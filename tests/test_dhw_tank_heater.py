"""TDD for DHW tank heater: permission switch + active indicator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_platform_creates_switch_and_binary_sensor():
    """Platform should add exactly one switch and one binary sensor for DHW tank heater."""
    # Import platforms lazily
    from custom_components.gree_versati.switch import (
        async_setup_entry as switch_setup,
    )
    from custom_components.gree_versati.binary_sensor import (
        async_setup_entry as bs_setup,
    )

    # Coordinator mock
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "versati_series": "III",
        # permission and active flags expected from coordinator
        "allow_tank_heater": False,
        "tank_heater_active": False,
    }
    coordinator.config_entry.entry_id = "entry123"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

    # Mock entry wrapper used by platforms
    entry = MagicMock()
    entry.runtime_data.coordinator = coordinator

    async_add_entities_switch = MagicMock()
    async_add_entities_bs = MagicMock()

    await switch_setup(MagicMock(), entry, async_add_entities_switch)
    await bs_setup(MagicMock(), entry, async_add_entities_bs)

    # Validate entities are created
    sw_entities = list(async_add_entities_switch.call_args[0][0])
    bs_entities = list(async_add_entities_bs.call_args[0][0])

    assert len(sw_entities) >= 1
    assert len(bs_entities) >= 1


@pytest.mark.asyncio
async def test_switch_toggles_permission_and_refreshes():
    """Turning switch on/off calls client.set_allow_tank_heater and refreshes."""
    from custom_components.gree_versati.switch import async_setup_entry as switch_setup

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"allow_tank_heater": False, "tank_heater_active": False}
    coordinator.async_request_refresh = AsyncMock()
    coordinator.config_entry.entry_id = "entry123"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"
    client = coordinator.config_entry.runtime_data.client
    client.set_allow_tank_heater = AsyncMock()

    entry = MagicMock()
    entry.runtime_data.coordinator = coordinator

    async_add_entities_switch = MagicMock()
    await switch_setup(MagicMock(), entry, async_add_entities_switch)
    switch_entity = list(async_add_entities_switch.call_args[0][0])[0]

    # Turn on -> True
    await switch_entity.async_turn_on()
    client.set_allow_tank_heater.assert_awaited_with(True)
    coordinator.async_request_refresh.assert_awaited()

    # Turn off -> False
    client.set_allow_tank_heater.reset_mock()
    coordinator.async_request_refresh.reset_mock()
    await switch_entity.async_turn_off()
    client.set_allow_tank_heater.assert_awaited_with(False)
    coordinator.async_request_refresh.assert_awaited()


@pytest.mark.asyncio
async def test_binary_sensor_reflects_active_status_read_only():
    """Binary sensor state follows tank_heater_active and has no toggle methods."""
    from custom_components.gree_versati.binary_sensor import (
        async_setup_entry as bs_setup,
    )

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"tank_heater_active": True}
    coordinator.config_entry.entry_id = "entry123"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"

    entry = MagicMock()
    entry.runtime_data.coordinator = coordinator

    async_add_entities_bs = MagicMock()
    await bs_setup(MagicMock(), entry, async_add_entities_bs)
    bs_entity = list(async_add_entities_bs.call_args[0][0])[0]

    assert getattr(bs_entity, "is_on") is True
    # Ensure there are no turn_on/turn_off on binary sensor
    assert not hasattr(bs_entity, "async_turn_on")
    assert not hasattr(bs_entity, "async_turn_off")
