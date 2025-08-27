"""TDD: Wiring tests for combined mode control via entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.climate.const import HVACMode

from custom_components.gree_versati.const import COOL_MODE, HEAT_MODE


def _make_coordinator():
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.set_device_mode = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {}
    return coordinator


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hvac,fast,expected",
    [
        (HVACMode.OFF, False, "off"),
        (HVACMode.OFF, True, "hot_water"),
        (HVACMode.HEAT, False, "heat"),
        (HVACMode.HEAT, True, "heat_hot_water"),
        (HVACMode.COOL, False, "cool"),
        (HVACMode.COOL, True, "cool_hot_water"),
    ],
)
async def test_climate_async_set_hvac_mode_combines_to_device_mode(
    hvac, fast, expected
):
    """Setting climate hvac_mode should map to combined device mode based on DHW flag."""
    from custom_components.gree_versati.climate import GreeVersatiClimate

    coordinator = _make_coordinator()
    coordinator.data["fast_heat_water"] = fast

    entity = GreeVersatiClimate(coordinator)

    await entity.async_set_hvac_mode(hvac)

    # Expectation: combined mode is selected via client.set_device_mode
    coordinator.config_entry.runtime_data.client.set_device_mode.assert_awaited_once_with(
        expected
    )
    coordinator.async_request_refresh.assert_awaited_once()


def _hvac_from_data(power: bool, mode_val: int) -> str:
    if not power:
        return "off"
    if mode_val == HEAT_MODE:
        return "heat"
    if mode_val == COOL_MODE:
        return "cool"
    return "off"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "power,mode_val,op_mode,expected",
    [
        (False, HEAT_MODE, "performance", "hot_water"),
        (True, HEAT_MODE, "performance", "heat_hot_water"),
        (True, COOL_MODE, "performance", "cool_hot_water"),
        (False, HEAT_MODE, "normal", "off"),
        (True, HEAT_MODE, "normal", "heat"),
        (True, COOL_MODE, "normal", "cool"),
    ],
)
async def test_water_heater_async_set_operation_mode_combines(
    power, mode_val, op_mode, expected
):
    """Setting DHW operation should map to combined device mode based on HVAC power/mode."""
    from custom_components.gree_versati.water_heater import GreeVersatiWaterHeater

    coordinator = _make_coordinator()
    coordinator.data["power"] = power
    coordinator.data["mode"] = mode_val

    entity = GreeVersatiWaterHeater(coordinator)

    await entity.async_set_operation_mode(op_mode)

    coordinator.config_entry.runtime_data.client.set_device_mode.assert_awaited_once_with(
        expected
    )
    coordinator.async_request_refresh.assert_awaited_once()
