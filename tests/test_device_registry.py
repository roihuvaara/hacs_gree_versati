"""Test device registry integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.gree_versati.climate import GreeVersatiClimate
from custom_components.gree_versati.const import DOMAIN
from custom_components.gree_versati.water_heater import GreeVersatiWaterHeater


def test_device_info_comparison():
    """Test that climate and water_heater entities have different device_info (the bug)."""
    # Create a mock coordinator and client
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"
    coordinator.config_entry.title = "Test Device"
    coordinator.data = {"versati_series": "III"}

    client = MagicMock()
    client.mac = "AA:BB:CC:DD:EE:FF"

    # Create both entities as they currently exist
    climate_entity = GreeVersatiClimate(coordinator, client)
    water_heater_entity = GreeVersatiWaterHeater(coordinator, client)

    # Get their device_info
    climate_device_info = climate_entity.device_info
    water_heater_device_info = water_heater_entity.device_info

    print(f"Climate device info: {climate_device_info}")
    print(f"Water heater device info: {water_heater_device_info}")

    # Check if they have the same identifiers (they should, but currently don't)
    climate_identifiers = (
        climate_device_info.get("identifiers") if climate_device_info else None
    )
    water_heater_identifiers = (
        water_heater_device_info.get("identifiers")
        if water_heater_device_info
        else None
    )

    print(f"Climate identifiers: {climate_identifiers}")
    print(f"Water heater identifiers: {water_heater_identifiers}")

    # The critical test: Do both entities provide the same device identifiers?
    # If they do, they'll be grouped as one device. If not, they'll be separate devices.

    identifiers_match = climate_identifiers == water_heater_identifiers
    print(f"Identifiers match: {identifiers_match}")

    # COUNT how many unique device identifiers we have
    unique_identifiers = set()
    if climate_identifiers:
        unique_identifiers.add(frozenset(climate_identifiers))
    if water_heater_identifiers:
        unique_identifiers.add(frozenset(water_heater_identifiers))

    device_count = len(unique_identifiers)
    print(f"Unique device identifier sets: {device_count}")

    assert device_count == 1, (
        f"Expected exactly 1 unique device identifier set, found {device_count}. "
    )
