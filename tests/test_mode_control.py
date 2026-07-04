"""Mode control tests for combined device modes (TDD)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.gree_versati.const import (
    MODE_COOL,
    MODE_HEAT,
    MODE_HOT_WATER,
)
from custom_components.gree_versati.protocol import AwhpProps


@pytest.mark.asyncio
async def test_client_has_set_device_mode_api():
    """Client should expose set_device_mode(mode) for 6 modes."""
    # Import lazily to avoid circulars
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    # Method exists
    assert hasattr(client, "set_device_mode")


@pytest.mark.asyncio
async def test_hw_only_mapping_sets_mod_correctly():
    """Selecting HOT_WATER should write Mod=2 (hot water only) and power on."""
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    # Attach a fake device with needed API
    device = MagicMock()
    device.set_property = MagicMock()
    device.push_state_update = AsyncMock()
    client.device = device

    # Provide minimal internal data structure for follow-up refresh
    client._data = {}

    # Execute: set HW-only mode
    client.async_get_data = AsyncMock(return_value={})
    await client.set_device_mode("hot_water")

    # Assert: hot water is a first-class Mod value, not a FastHtWter flag
    device.set_property.assert_any_call(AwhpProps.MODE, MODE_HOT_WATER)
    device.set_property.assert_any_call(AwhpProps.POWER, value=True)
    for call in device.set_property.call_args_list:
        assert call.args[0] != AwhpProps.FAST_HEAT_WATER, (
            "FastHtWter is the boost flag and must not be touched by mode changes"
        )
    device.push_state_update.assert_awaited()


@pytest.mark.asyncio
async def test_set_device_mode_off_before_mode_when_on():
    """When device is ON and target mode changes, enforce OFF -> MODE -> ON sequence."""
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    # Fake device and record calls
    events: list[tuple[str, object]] = []

    def record(prop: AwhpProps, *args, **kwargs):
        if prop == AwhpProps.POWER:
            events.append(("POWER", kwargs.get("value")))
        elif prop == AwhpProps.MODE:
            events.append(("MODE", args[0] if args else kwargs.get("value")))
        else:
            events.append((prop.name, args[0] if args else kwargs.get("value")))

    device = MagicMock()
    device.set_property = MagicMock(side_effect=record)
    device.push_state_update = AsyncMock()
    client.device = device
    # Current state: ON in COOL
    client._data = {"power": True, "mode": MODE_COOL}
    client.async_get_data = AsyncMock(return_value={})

    await client.set_device_mode("heat")

    # Extract ordering indices
    idx_power_off = next(
        (i for i, (k, v) in enumerate(events) if k == "POWER" and v is False), None
    )
    idx_mode = next((i for i, (k, _) in enumerate(events) if k == "MODE"), None)
    idx_power_on = next(
        (i for i, (k, v) in enumerate(events) if k == "POWER" and v is True), None
    )

    assert idx_power_off is not None, "Expected POWER False before changing mode"
    assert idx_mode is not None, "Expected MODE to be set"
    assert idx_power_on is not None, "Expected POWER True after changing mode"
    assert idx_power_off < idx_mode < idx_power_on, (
        f"Order must be OFF -> MODE -> ON, got events: {events}"
    )
    # The OFF, MODE and ON steps must each be pushed to the device
    # separately, otherwise only the final state ever reaches the unit.
    assert device.push_state_update.await_count >= 3


@pytest.mark.asyncio
async def test_set_device_mode_writes_correct_mod_values():
    """Each logical mode writes its Versati Mod value (not the AC table)."""
    from custom_components.gree_versati.client import GreeVersatiClient

    expected = {
        "heat": 1,
        "hot_water": 2,
        "cool_hot_water": 3,
        "heat_hot_water": 4,
        "cool": 5,
    }
    for mode, mod_value in expected.items():
        client = GreeVersatiClient()
        device = MagicMock()
        device.set_property = MagicMock()
        device.push_state_update = AsyncMock()
        client.device = device
        client._data = {"power": False, "mode": None}
        client.async_get_data = AsyncMock(return_value={})

        await client.set_device_mode(mode)

        device.set_property.assert_any_call(AwhpProps.MODE, mod_value)


@pytest.mark.asyncio
async def test_set_device_mode_when_off_sets_mode_then_on():
    """When device is OFF, set MODE then POWER ON (no POWER OFF call)."""
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    events: list[tuple[str, object]] = []

    def record(prop: AwhpProps, *args, **kwargs):
        if prop == AwhpProps.POWER:
            events.append(("POWER", kwargs.get("value")))
        elif prop == AwhpProps.MODE:
            events.append(("MODE", args[0] if args else kwargs.get("value")))
        else:
            events.append((prop.name, args[0] if args else kwargs.get("value")))

    device = MagicMock()
    device.set_property = MagicMock(side_effect=record)
    device.push_state_update = AsyncMock()
    client.device = device
    client._data = {"power": False, "mode": MODE_COOL}
    client.async_get_data = AsyncMock(return_value={})

    await client.set_device_mode("heat")

    # There should be no POWER False
    assert ("POWER", False) not in events
    # MODE should appear before POWER True
    idx_mode = next(i for i, (k, _) in enumerate(events) if k == "MODE")
    idx_power_on = next(
        i for i, (k, v) in enumerate(events) if k == "POWER" and v is True
    )
    assert idx_mode < idx_power_on


@pytest.mark.asyncio
async def test_set_device_mode_updates_cache_optimistically():
    """The client cache reflects the commanded state without a poll."""
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    device = MagicMock()
    device.set_property = MagicMock()
    device.push_state_update = AsyncMock()
    client.device = device
    client._data = {"power": True, "mode": MODE_HEAT, "hot_water_temp": 50.0}
    # Polling right after a mode change would read transitional values
    client.async_get_data = AsyncMock(
        side_effect=AssertionError("must not poll mid-transition")
    )

    await client.set_device_mode("heat_hot_water")
    assert client._data["power"] is True
    assert client._data["mode"] == 4
    assert client._data["hot_water_temp"] == 50.0

    await client.set_device_mode("off")
    assert client._data["power"] is False


@pytest.mark.asyncio
async def test_set_device_mode_off_always_powers_off():
    """Selecting OFF always results in POWER False."""
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    events: list[tuple[str, object]] = []

    def record(prop: AwhpProps, *args, **kwargs):
        if prop == AwhpProps.POWER:
            events.append(("POWER", kwargs.get("value")))
        elif prop == AwhpProps.MODE:
            events.append(("MODE", args[0] if args else kwargs.get("value")))
        else:
            events.append((prop.name, args[0] if args else kwargs.get("value")))

    device = MagicMock()
    device.set_property = MagicMock(side_effect=record)
    device.push_state_update = AsyncMock()
    client.device = device
    client._data = {"power": True, "mode": MODE_HEAT}
    client.async_get_data = AsyncMock(return_value={})

    await client.set_device_mode("off")

    assert ("POWER", False) in events
