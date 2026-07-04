"""Tests for the Gree Versati sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.gree_versati.sensor import (
    SENSOR_DESCRIPTIONS,
    GreeVersatiSensor,
    async_setup_entry,
)


def _make_coordinator(data: dict | None = None):
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.data = data if data is not None else {}
    return coordinator


def _description(key: str):
    return next(d for d in SENSOR_DESCRIPTIONS if d.key == key)


def test_descriptions_cover_expected_keys():
    """All graphable temperatures are exposed as sensors."""
    keys = {d.key for d in SENSOR_DESCRIPTIONS}
    assert keys == {
        "hot_water_temp",
        "water_out_temp",
        "water_in_temp",
        "opt_water_temp",
    }
    # Every sensor must produce long-term statistics for history graphs
    assert all(d.state_class == "measurement" for d in SENSOR_DESCRIPTIONS)


def test_native_value_reads_coordinator_data():
    """Sensor value comes straight from coordinator data by key."""
    coordinator = _make_coordinator({"hot_water_temp": 52.5})
    sensor = GreeVersatiSensor(coordinator, _description("hot_water_temp"))

    assert sensor.native_value == 52.5
    assert sensor._attr_unique_id == "test_entry_id_hot_water_temp"


def test_native_value_missing_is_none():
    """Missing data yields None (entity shows unknown)."""
    coordinator = _make_coordinator({})
    sensor = GreeVersatiSensor(coordinator, _description("water_out_temp"))

    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_async_setup_entry_adds_all_sensors():
    """Platform setup adds one entity per description."""
    hass = MagicMock()
    entry = MagicMock()
    entry.runtime_data.coordinator = _make_coordinator()
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = list(async_add_entities.call_args[0][0])
    assert len(entities) == len(SENSOR_DESCRIPTIONS)
    assert all(isinstance(e, GreeVersatiSensor) for e in entities)
