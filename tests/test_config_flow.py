"""Test the Gree Versati config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from gree_versati.awhp_device import AwhpDevice
from gree_versati.deviceinfo import DeviceInfo
from homeassistant import config_entries
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT

from custom_components.gree_versati.const import CONF_IP, DOMAIN


@pytest.mark.asyncio
async def test_form(hass):
    """Test we get the form."""
    # Create a mock device for discovery
    mock_device_info = MagicMock(spec=DeviceInfo)
    mock_device_info.ip = "192.168.1.123"
    mock_device_info.port = 7000
    mock_device_info.mac = "AA:BB:CC:DD:EE:FF"
    mock_device_info.name = "Test Device"

    mock_device = MagicMock(spec=AwhpDevice)
    mock_device.device_info = mock_device_info
    mock_device.bind = AsyncMock(return_value="test_key")

    # Mock the discovery and setup
    with (
        patch(
            "custom_components.gree_versati.client.GreeVersatiClient.run_discovery",
            return_value=[mock_device],
        ),
        patch.object(hass, "async_add_executor_job", new_callable=AsyncMock),
    ):
        # First step - user form
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["errors"] == {}

        # Submit the user form (this should lead to the bind step)
        bind_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},  # No input needed for the first step
        )

        # The flow should now be in the bind step
        assert bind_result["type"] == "form"

        # Now we need to simulate the bind step
        # In our mock, we're patching the flow to return a create_entry result
        # when we provide a MAC address
        final_result = await hass.config_entries.flow.async_configure(
            bind_result["flow_id"],
            {"mac": "AA:BB:CC:DD:EE:FF"},
        )

        await hass.async_block_till_done()

    # Check the final result
    assert final_result["type"] == "create_entry"
    assert final_result["title"] == "Test Device"
    assert final_result["data"] == {
        CONF_IP: "192.168.1.123",
        CONF_PORT: 7000,
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_NAME: "Test Device",
        "key": "test_key",
    }
