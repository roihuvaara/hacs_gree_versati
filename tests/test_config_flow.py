"""Test the Gree Versati config flow."""
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_PORT
from custom_components.gree_versati.const import DOMAIN

async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.gree_versati.config_flow.GreeVersatiClient.validate_connection",
        return_value=True,
    ), patch(
        "custom_components.gree_versati.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.123",
                CONF_PORT: 7000,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "192.168.1.123"
    assert result2["data"] == {
        CONF_HOST: "192.168.1.123",
        CONF_PORT: 7000,
    }
    assert len(mock_setup_entry.mock_calls) == 1 