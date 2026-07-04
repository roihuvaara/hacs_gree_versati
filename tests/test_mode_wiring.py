"""TDD: Wiring tests for combined mode control via entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.climate.const import HVACMode

from custom_components.gree_versati.const import (
    MODE_COOL,
    MODE_COOL_HOT_WATER,
    MODE_HEAT,
    MODE_HEAT_HOT_WATER,
    MODE_HOT_WATER,
    OPERATION_MODE_HEAT_PUMP,
    OPERATION_MODE_OFF,
    OPERATION_MODE_PERFORMANCE,
)


def _make_coordinator():
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.config_entry.runtime_data.client.set_device_mode = AsyncMock()
    coordinator.config_entry.runtime_data.client.set_dhw_mode = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {}
    return coordinator


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hvac,power,mode_val,expected",
    [
        # DHW inactive: plain modes
        (HVACMode.OFF, True, MODE_HEAT, "off"),
        (HVACMode.HEAT, False, MODE_HEAT, "heat"),
        (HVACMode.HEAT, True, MODE_COOL, "heat"),
        (HVACMode.COOL, True, MODE_HEAT, "cool"),
        # DHW active (current Mod includes hot water): keep it in the mode
        (HVACMode.OFF, True, MODE_HEAT_HOT_WATER, "hot_water"),
        (HVACMode.OFF, True, MODE_HOT_WATER, "hot_water"),
        (HVACMode.HEAT, True, MODE_HEAT_HOT_WATER, "heat_hot_water"),
        (HVACMode.HEAT, True, MODE_HOT_WATER, "heat_hot_water"),
        (HVACMode.COOL, True, MODE_COOL_HOT_WATER, "cool_hot_water"),
        # Device off: DHW not active even if last Mod included hot water
        (HVACMode.HEAT, False, MODE_HEAT_HOT_WATER, "heat"),
    ],
)
async def test_climate_async_set_hvac_mode_combines_to_device_mode(
    hvac, power, mode_val, expected
):
    """Setting climate hvac_mode maps to combined device mode based on DHW state."""
    from custom_components.gree_versati.climate import GreeVersatiClimate

    coordinator = _make_coordinator()
    coordinator.data["power"] = power
    coordinator.data["mode"] = mode_val

    entity = GreeVersatiClimate(coordinator)

    await entity.async_set_hvac_mode(hvac)

    # Expectation: combined mode is selected via client.set_device_mode
    coordinator.config_entry.runtime_data.client.set_device_mode.assert_awaited_once_with(
        expected
    )
    coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "power,mode_val,op_mode,expected,expected_boost",
    [
        # DHW on while space heating/cooling runs: combined modes
        (True, MODE_HEAT, OPERATION_MODE_HEAT_PUMP, "heat_hot_water", "normal"),
        (True, MODE_HEAT, OPERATION_MODE_PERFORMANCE, "heat_hot_water", "performance"),
        (True, MODE_COOL, OPERATION_MODE_PERFORMANCE, "cool_hot_water", "performance"),
        (
            True,
            MODE_HEAT_HOT_WATER,
            OPERATION_MODE_PERFORMANCE,
            "heat_hot_water",
            "performance",
        ),
        # DHW on while device off: hot water only
        (False, MODE_HEAT, OPERATION_MODE_HEAT_PUMP, "hot_water", "normal"),
        (False, MODE_HEAT, OPERATION_MODE_PERFORMANCE, "hot_water", "performance"),
        # DHW off: strip hot water from the mode
        (True, MODE_HEAT_HOT_WATER, OPERATION_MODE_OFF, "heat", None),
        (True, MODE_COOL_HOT_WATER, OPERATION_MODE_OFF, "cool", None),
        (True, MODE_HOT_WATER, OPERATION_MODE_OFF, "off", None),
        (False, MODE_HEAT, OPERATION_MODE_OFF, "off", None),
    ],
)
async def test_water_heater_async_set_operation_mode_combines(
    power, mode_val, op_mode, expected, expected_boost
):
    """Setting DHW operation maps to combined device mode based on HVAC power/mode."""
    from custom_components.gree_versati.water_heater import GreeVersatiWaterHeater

    coordinator = _make_coordinator()
    coordinator.data["power"] = power
    coordinator.data["mode"] = mode_val

    entity = GreeVersatiWaterHeater(coordinator)

    await entity.async_set_operation_mode(op_mode)

    client = coordinator.config_entry.runtime_data.client
    client.set_device_mode.assert_awaited_once_with(expected)
    if expected_boost is None:
        client.set_dhw_mode.assert_not_awaited()
    else:
        client.set_dhw_mode.assert_awaited_once_with(expected_boost)
    coordinator.async_request_refresh.assert_awaited_once()
