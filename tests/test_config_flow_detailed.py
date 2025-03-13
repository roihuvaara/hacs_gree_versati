"""Test the config flow for the Gree Versati integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType

from custom_components.gree_versati.config_flow import GreeVersatiConfigFlow
from custom_components.gree_versati.const import CONF_IP


@pytest.fixture
def mock_discovery():
    """Mock the discovery process."""
    with patch(
        "custom_components.gree_versati.client.GreeVersatiClient.run_discovery"
    ) as mock_discovery:
        yield mock_discovery


@pytest.fixture
def mock_device():
    """Create a mock device."""
    device = MagicMock()
    device.device_info.mac = "AA:BB:CC:DD:EE:FF"
    device.device_info.ip = "192.168.1.100"
    device.device_info.port = 7000
    device.device_info.name = "Test Device"
    device.name = "Test Device"
    device.ip = "192.168.1.100"
    device.bind = AsyncMock(return_value="test_key")
    return device


class TestGreeVersatiConfigFlow:
    """Test the Gree Versati config flow."""

    async def test_user_step_no_devices(self, mock_discovery):
        """Test the user step when no devices are found."""
        # Mock discovery to return no devices
        mock_discovery.return_value = []

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the user step
        result = await flow.async_step_user({})

        # Verify the result
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "user"
        assert result.get("errors") == {"base": "no_devices_found"}

    async def test_user_step_discovery_error(self, mock_discovery):
        """Test the user step when discovery fails."""
        # Mock discovery to raise an exception
        mock_discovery.side_effect = Exception("Test error")

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the user step
        result = await flow.async_step_user({})

        # Verify the result
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "user"
        assert result.get("errors") == {"base": "cannot_connect"}

    async def test_user_step_one_device(self, mock_discovery, mock_device):
        """Test the user step when one device is found."""
        # Mock discovery to return one device
        mock_discovery.return_value = [mock_device]

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the user step
        with patch.object(flow, "async_step_bind") as mock_bind_step:
            mock_bind_step.return_value = {"type": "create_entry"}
            _ = await flow.async_step_user({})

            # Verify bind step was called with the correct MAC
            mock_bind_step.assert_called_once_with({"mac": "AA:BB:CC:DD:EE:FF"})

    async def test_user_step_multiple_devices(self, mock_discovery, mock_device):
        """Test the user step when multiple devices are found."""
        # Create a second mock device
        device2 = MagicMock()
        device2.device_info.mac = "11:22:33:44:55:66"
        device2.name = "Test Device 2"
        device2.ip = "192.168.1.101"

        # Mock discovery to return multiple devices
        mock_discovery.return_value = [mock_device, device2]

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the user step
        result = await flow.async_step_user({})

        # Verify the result
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "select_device"

        # Check if data_schema exists and has mac in its schema
        data_schema = result.get("data_schema")
        assert data_schema is not None
        assert "mac" in data_schema.schema

    async def test_select_device_step(self, mock_discovery, mock_device):
        """Test the select_device step."""
        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the select_device step
        with patch.object(flow, "async_step_bind") as mock_bind_step:
            mock_bind_step.return_value = {"type": "create_entry"}
            _ = await flow.async_step_select_device({"mac": "AA:BB:CC:DD:EE:FF"})

            # Verify bind step was called with the correct MAC
            mock_bind_step.assert_called_once_with({"mac": "AA:BB:CC:DD:EE:FF"})

    async def test_select_device_step_no_input(self, mock_discovery):
        """Test the select_device step with no input."""
        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the select_device step with no input
        with patch.object(flow, "async_step_user") as mock_user_step:
            mock_user_step.return_value = {"type": "form"}
            _ = await flow.async_step_select_device(None)

            # Verify user step was called
            mock_user_step.assert_called_once()

    async def test_bind_step_success(self, mock_discovery, mock_device):
        """Test the bind step when successful."""
        # Mock discovery to return the device
        mock_discovery.return_value = [mock_device]

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Mock the async_set_unique_id method
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        # Call the bind step
        result = await flow.async_step_bind({"mac": "AA:BB:CC:DD:EE:FF"})

        # Verify the result
        assert result.get("type") == FlowResultType.CREATE_ENTRY
        assert result.get("title") == "Gree Versati"
        assert result.get("data") == {
            CONF_IP: "192.168.1.100",
            CONF_PORT: 7000,
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_NAME: "Test Device",
            "key": "test_key",
        }

        # Verify unique ID was set
        flow.async_set_unique_id.assert_called_once_with("AA:BB:CC:DD:EE:FF")
        flow._abort_if_unique_id_configured.assert_called_once()

    async def test_bind_step_no_mac(self, mock_discovery):
        """Test the bind step with no MAC address."""
        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the bind step with no MAC
        result = await flow.async_step_bind({})

        # Verify the result
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "invalid_device"

    async def test_bind_step_discovery_error(self, mock_discovery):
        """Test the bind step when discovery fails."""
        # Mock discovery to raise an exception
        mock_discovery.side_effect = Exception("Test error")

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the bind step
        result = await flow.async_step_bind({"mac": "AA:BB:CC:DD:EE:FF"})

        # Verify the result
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "cannot_connect"

    async def test_bind_step_device_not_found(self, mock_discovery):
        """Test the bind step when the device is not found."""
        # Mock discovery to return no devices
        mock_discovery.return_value = []

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the bind step
        result = await flow.async_step_bind({"mac": "AA:BB:CC:DD:EE:FF"})

        # Verify the result
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "device_not_found"

    async def test_bind_step_bind_error(self, mock_discovery, mock_device):
        """Test the bind step when binding fails."""
        # Mock discovery to return the device
        mock_discovery.return_value = [mock_device]

        # Mock the bind method to raise an exception
        mock_device.bind.side_effect = Exception("Bind error")

        # Initialize the config flow
        flow = GreeVersatiConfigFlow()

        # Call the bind step
        result = await flow.async_step_bind({"mac": "AA:BB:CC:DD:EE:FF"})

        # Verify the result
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "bind_failed"
