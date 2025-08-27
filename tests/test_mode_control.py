"""Mode control tests for combined device modes (TDD)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


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
    with pytest.raises(Exception):
        # Expect failure for now (TDD) until implemented
        await client.set_device_mode("hot_water")




