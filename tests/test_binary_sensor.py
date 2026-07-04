"""Tests for the Gree Versati binary sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.gree_versati.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    GreeVersatiBinarySensor,
    async_setup_entry,
)


def _make_coordinator(data: dict | None = None):
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.runtime_data.client = MagicMock()
    coordinator.data = data if data is not None else {}
    return coordinator


def _description(key: str):
    return next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == key)


def test_descriptions_cover_expected_keys():
    """All running-state flags are exposed as binary sensors."""
    keys = {d.key for d in BINARY_SENSOR_DESCRIPTIONS}
    assert keys == {
        "tank_heater_status",
        "hp_heater_1_status",
        "hp_heater_2_status",
        "defrosting_status",
        "frost_protection",
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1, True), (True, True), (0, False), (False, False), (None, None)],
)
def test_is_on_conversion(raw, expected):
    """Device ints become booleans; missing values stay unknown."""
    coordinator = _make_coordinator({"tank_heater_status": raw})
    sensor = GreeVersatiBinarySensor(coordinator, _description("tank_heater_status"))

    assert sensor.is_on is expected


def test_unique_id():
    """Unique ids are entry-scoped per key."""
    coordinator = _make_coordinator()
    sensor = GreeVersatiBinarySensor(coordinator, _description("defrosting_status"))
    assert sensor._attr_unique_id == "test_entry_id_defrosting_status"


@pytest.mark.asyncio
async def test_async_setup_entry_adds_all_binary_sensors():
    """Platform setup adds one entity per description."""
    hass = MagicMock()
    entry = MagicMock()
    entry.runtime_data.coordinator = _make_coordinator()
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    entities = list(async_add_entities.call_args[0][0])
    assert len(entities) == len(BINARY_SENSOR_DESCRIPTIONS)
    assert all(isinstance(e, GreeVersatiBinarySensor) for e in entities)
