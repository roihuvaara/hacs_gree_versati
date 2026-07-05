"""Test the Gree Versati options flow (temperature limits)."""

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gree_versati.config_flow import (
    GreeVersatiConfigFlow,
    GreeVersatiOptionsFlow,
)
from custom_components.gree_versati.const import (
    CONF_COOL_TEMP_MAX,
    CONF_COOL_TEMP_MIN,
    CONF_DHW_TEMP_MAX,
    CONF_DHW_TEMP_MIN,
    CONF_HEAT_TEMP_MAX,
    CONF_HEAT_TEMP_MIN,
    DOMAIN,
)


def _make_flow(options: dict | None = None) -> GreeVersatiOptionsFlow:
    """Create an options flow bound to a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"ip": "192.168.1.100", "port": 7000, "mac": "AA:BB:CC:DD:EE:FF"},
        options=options or {},
        entry_id="test_entry",
    )
    flow = GreeVersatiOptionsFlow()
    flow.handler = entry.entry_id
    flow.hass = MagicMock()
    flow.hass.config_entries.async_get_known_entry.return_value = entry
    return flow


def test_config_flow_registers_options_flow():
    """The config flow exposes the options flow handler."""
    entry = MagicMock()
    flow = GreeVersatiConfigFlow.async_get_options_flow(entry)
    assert isinstance(flow, GreeVersatiOptionsFlow)


@pytest.mark.asyncio
async def test_options_form_defaults_to_device_limits():
    """With no stored options the form defaults to the device limits."""
    flow = _make_flow()

    result = await flow.async_step_init()

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    defaults = {str(key): key.default() for key in schema}
    assert defaults == {
        CONF_HEAT_TEMP_MIN: 20,
        CONF_HEAT_TEMP_MAX: 60,
        CONF_COOL_TEMP_MIN: 7,
        CONF_COOL_TEMP_MAX: 25,
        CONF_DHW_TEMP_MIN: 40,
        CONF_DHW_TEMP_MAX: 80,
    }


@pytest.mark.asyncio
async def test_options_form_defaults_to_stored_options():
    """Previously saved options come back as the form defaults."""
    flow = _make_flow({CONF_HEAT_TEMP_MAX: 55, CONF_DHW_TEMP_MIN: 45})

    result = await flow.async_step_init()

    schema = result["data_schema"].schema
    defaults = {str(key): key.default() for key in schema}
    assert defaults[CONF_HEAT_TEMP_MAX] == 55
    assert defaults[CONF_DHW_TEMP_MIN] == 45
    # Untouched fields still default to device limits
    assert defaults[CONF_HEAT_TEMP_MIN] == 20
    assert defaults[CONF_DHW_TEMP_MAX] == 80


@pytest.mark.asyncio
async def test_options_saved_as_ints():
    """Submitting the form stores whole-degree ints (selector emits floats)."""
    flow = _make_flow()

    result = await flow.async_step_init(
        {
            CONF_HEAT_TEMP_MIN: 25.0,
            CONF_HEAT_TEMP_MAX: 55.0,
            CONF_COOL_TEMP_MIN: 10.0,
            CONF_COOL_TEMP_MAX: 20.0,
            CONF_DHW_TEMP_MIN: 45.0,
            CONF_DHW_TEMP_MAX: 65.0,
        }
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_HEAT_TEMP_MIN: 25,
        CONF_HEAT_TEMP_MAX: 55,
        CONF_COOL_TEMP_MIN: 10,
        CONF_COOL_TEMP_MAX: 20,
        CONF_DHW_TEMP_MIN: 45,
        CONF_DHW_TEMP_MAX: 65,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("min_key", "max_key", "error"),
    [
        (CONF_HEAT_TEMP_MIN, CONF_HEAT_TEMP_MAX, "heat_min_above_max"),
        (CONF_COOL_TEMP_MIN, CONF_COOL_TEMP_MAX, "cool_min_above_max"),
        (CONF_DHW_TEMP_MIN, CONF_DHW_TEMP_MAX, "dhw_min_above_max"),
    ],
)
async def test_options_min_above_max_shows_error(min_key, max_key, error):
    """A minimum above its maximum re-shows the form with an error."""
    valid = {
        CONF_HEAT_TEMP_MIN: 20,
        CONF_HEAT_TEMP_MAX: 60,
        CONF_COOL_TEMP_MIN: 7,
        CONF_COOL_TEMP_MAX: 25,
        CONF_DHW_TEMP_MIN: 40,
        CONF_DHW_TEMP_MAX: 80,
    }
    user_input = {**valid, min_key: valid[max_key] + 1}
    flow = _make_flow()

    result = await flow.async_step_init(user_input)

    assert result["type"] == "form"
    assert result["errors"] == {"base": error}
