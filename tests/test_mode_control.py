"""Mode control tests for combined device modes (TDD)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.gree_versati.const import COOL_MODE, HEAT_MODE
from gree_versati.awhp_device import AwhpProps


@pytest.mark.asyncio
async def test_client_has_set_device_mode_api():
    """Client should expose set_device_mode(mode) for 6 modes."""
    # Import lazily to avoid circulars
    from custom_components.gree_versati.client import GreeVersatiClient

    client = GreeVersatiClient()
    # Method exists
    assert hasattr(client, "set_device_mode")


@pytest.mark.asyncio
async def test_hw_only_mapping_sets_flags_correctly():
    """Selecting HOT_WATER should set device power on and DHW flag, climate mode off."""
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

    # Assert: correct properties were set
    device.set_property.assert_any_call(AwhpProps.MODE, HEAT_MODE)
    device.set_property.assert_any_call(AwhpProps.POWER, value=True)
    device.set_property.assert_any_call(AwhpProps.FAST_HEAT_WATER, value=True)
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
    client._data = {"power": True, "mode": COOL_MODE}
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
    client._data = {"power": False, "mode": COOL_MODE}
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
    client._data = {"power": True, "mode": HEAT_MODE}
    client.async_get_data = AsyncMock(return_value={})

    await client.set_device_mode("off")

    assert ("POWER", False) in events
