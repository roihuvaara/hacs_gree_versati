"""Tests for the config flow's handling of device discovery."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType

from custom_components.gree_versati.config_flow import GreeVersatiConfigFlow
from custom_components.gree_versati.const import CONF_IP


def assert_form_error(result: dict[str, Any] | None, step_id: str, error: str) -> None:
    """Assert that the result is a form with the expected error."""
    if result is None:
        pytest.fail("Result is None")
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == step_id
    errors = result.get("errors", {})
    assert errors
    assert errors.get("base") == error


def assert_abort(result: dict[str, Any] | None, reason: str) -> None:
    """Assert that the result is an abort with the expected reason."""
    if result is None:
        pytest.fail("Result is None")
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == reason


def assert_create_entry(
    result: dict[str, Any] | None, title: str, data: dict[str, Any]
) -> None:
    """Assert that the result is a create_entry with the expected data."""
    if result is None:
        pytest.fail("Result is None")
    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == title
    assert result.get("data") == data


@pytest.fixture
def mock_client():
    """Create a mock GreeVersatiClient."""
    client = MagicMock()
    client.run_discovery = AsyncMock()
    return client


@pytest.fixture
def mock_device():
    """Create a mock device."""
    device = MagicMock()
    device.device_info = MagicMock()
    device.device_info.mac = "AA:BB:CC:DD:EE:FF"
    device.device_info.ip = "192.168.1.100"
    device.device_info.port = 7000
    device.device_info.name = "Test Device"
    device.name = "Test Device"
    device.ip = "192.168.1.100"
    device.bind = AsyncMock(return_value="test_key")
    return device


@pytest.fixture
def mock_run_discovery():
    """Create a fixture to mock the client's run_discovery method."""
    with patch(
        "custom_components.gree_versati.client.GreeVersatiClient.run_discovery"
    ) as mock_run_discovery:
        yield mock_run_discovery


@pytest.mark.asyncio
async def test_user_step_no_devices(hass, mock_run_discovery):
    """Test the user step when no devices are found."""
    # Configure the mock to return no devices
    mock_run_discovery.return_value = []

    # Create flow and configure hass
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    # Call the method we're testing with empty dict instead of None
    result = await flow.async_step_user({})

    # Verify our mock was called
    mock_run_discovery.assert_called_once()

    # Check the result
    assert result is not None
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"
    errors = result.get("errors", {})
    assert errors is not None
    assert errors.get("base") == "no_devices_found"


@pytest.mark.asyncio
async def test_user_step_discovery_error(hass, mock_run_discovery):
    """Test the user step when discovery raises an error."""
    # Configure the mock to raise an exception
    mock_run_discovery.side_effect = Exception("Network error")

    # Create flow and configure hass
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    # Call the method we're testing with empty dict instead of None
    result = await flow.async_step_user({})

    # Verify our mock was called
    mock_run_discovery.assert_called_once()

    # Check the result
    assert result is not None
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"
    errors = result.get("errors", {})
    assert errors is not None
    assert errors.get("base") == "cannot_connect"


@pytest.mark.asyncio
async def test_user_step_one_device(hass, mock_run_discovery, mock_device):
    """Test the user step when one device is discovered."""
    # Configure the mock to return one device
    mock_run_discovery.return_value = [mock_device]

    # Create flow and configure hass
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    # Mock the async_set_unique_id method
    flow.async_set_unique_id = AsyncMock()

    # Create a mock schema for the bind step
    from unittest.mock import MagicMock

    import voluptuous as vol

    mock_schema = MagicMock()
    mock_schema.schema = {"mac": vol.Required("mac")}

    # Patch the bind step to return a form with a schema
    with patch.object(
        flow,
        "async_step_bind",
        return_value={
            "type": FlowResultType.FORM,
            "step_id": "bind",
            "data_schema": mock_schema,
        },
    ):
        # Call the method we're testing with empty dict instead of None
        result = await flow.async_step_user({})

        # Verify our mock was called
        mock_run_discovery.assert_called_once()

        # Check the result
        assert result is not None
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "bind"
        data_schema = result.get("data_schema")
        assert data_schema is not None
        assert "mac" in data_schema.schema


@pytest.mark.asyncio
async def test_user_step_multiple_devices(hass, mock_run_discovery):
    """Test the user step when multiple devices are discovered."""
    # Create mock devices
    device1 = MagicMock()
    device1.device_info = MagicMock()
    device1.device_info.mac = "AA:BB:CC:DD:EE:FF"
    device1.name = "Device 1"
    device1.ip = "192.168.1.100"

    device2 = MagicMock()
    device2.device_info = MagicMock()
    device2.device_info.mac = "11:22:33:44:55:66"
    device2.name = "Device 2"
    device2.ip = "192.168.1.101"

    # Configure the mock to return multiple devices
    mock_run_discovery.return_value = [device1, device2]

    # Create flow and configure hass
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    # Call the method we're testing with empty dict instead of None
    result = await flow.async_step_user({})

    # Verify our mock was called
    mock_run_discovery.assert_called_once()

    # Check the result
    assert result is not None
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "select_device"
    data_schema = result.get("data_schema")
    assert data_schema is not None
    assert "mac" in data_schema.schema


@pytest.mark.asyncio
async def test_select_device_step(hass):
    """Test the select_device step."""
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    # Mock the methods that would be called
    with (
        patch.object(
            flow, "async_step_user", return_value={"type": FlowResultType.FORM}
        ),
        patch.object(
            flow, "async_step_bind", return_value={"type": FlowResultType.FORM}
        ),
    ):
        result = await flow.async_step_select_device({"mac": "AA:BB:CC:DD:EE:FF"})
        assert result is not None
        assert result.get("type") == FlowResultType.FORM


@pytest.mark.asyncio
async def test_select_device_step_no_input(hass):
    """Test the select_device step with no user input."""
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    # Mock the method that would be called
    with patch.object(
        flow, "async_step_user", return_value={"type": FlowResultType.FORM}
    ):
        result = await flow.async_step_select_device()
        assert result is not None
        assert result.get("type") == FlowResultType.FORM


@pytest.mark.asyncio
async def test_bind_step_success(hass, mock_device):
    """Test the bind step with successful binding."""
    # Create a real mock client that will be returned when GreeVersatiClient is instantiated
    mock_client = MagicMock()
    mock_client.run_discovery = AsyncMock(return_value=[mock_device])

    # Use a direct patch on the GreeVersatiClient class rather than the import
    with patch(
        "custom_components.gree_versati.config_flow.GreeVersatiClient",
        return_value=mock_client,
    ):
        # Create and initialize the flow
        flow = GreeVersatiConfigFlow()
        flow.hass = hass
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock(return_value=None)

        # Call the method being tested
        result = await flow.async_step_bind(
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Device",
            }
        )

        # Verify expectations
        mock_client.run_discovery.assert_called_once()
        expected_data = {
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_IP: "192.168.1.100",
            CONF_PORT: 7000,
            CONF_NAME: "Test Device",
            "key": "test_key",
        }
        assert result is not None
        assert result.get("type") == FlowResultType.CREATE_ENTRY
        assert result.get("title") == "Gree Versati"
        assert result.get("data") == expected_data


@pytest.mark.asyncio
async def test_bind_step_no_mac(hass):
    """Test the bind step with no MAC address."""
    flow = GreeVersatiConfigFlow()
    flow.hass = hass

    result = await flow.async_step_bind(
        {
            "name": "Test Device",
        }
    )
    assert result is not None
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "invalid_device"


@pytest.mark.asyncio
async def test_bind_step_discovery_error(hass):
    """Test the bind step when discovery raises an error."""
    # Create a real mock client that will be returned when GreeVersatiClient is instantiated
    mock_client = MagicMock()
    mock_client.run_discovery = AsyncMock(side_effect=Exception("Network error"))

    # Use a direct patch on the GreeVersatiClient class rather than the import
    with patch(
        "custom_components.gree_versati.config_flow.GreeVersatiClient",
        return_value=mock_client,
    ):
        # Create and initialize the flow
        flow = GreeVersatiConfigFlow()
        flow.hass = hass

        # Call the method being tested
        result = await flow.async_step_bind(
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Device",
            }
        )

        # Verify expectations
        mock_client.run_discovery.assert_called_once()
        assert result is not None
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "cannot_connect"


@pytest.mark.asyncio
async def test_bind_step_device_not_found(hass):
    """Test the bind step when the device is not found."""
    # Create a real mock client that will be returned when GreeVersatiClient is instantiated
    mock_client = MagicMock()
    mock_client.run_discovery = AsyncMock(return_value=[])

    # Use a direct patch on the GreeVersatiClient class rather than the import
    with patch(
        "custom_components.gree_versati.config_flow.GreeVersatiClient",
        return_value=mock_client,
    ):
        # Create and initialize the flow
        flow = GreeVersatiConfigFlow()
        flow.hass = hass

        # Call the method being tested
        result = await flow.async_step_bind(
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Device",
            }
        )

        # Verify expectations
        mock_client.run_discovery.assert_called_once()
        assert result is not None
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "device_not_found"


@pytest.mark.asyncio
async def test_bind_step_bind_error(hass, mock_device):
    """Test the bind step when binding fails."""
    # Create a real mock client that will be returned when GreeVersatiClient is instantiated
    mock_client = MagicMock()
    mock_client.run_discovery = AsyncMock(return_value=[mock_device])
    # Configure the mock device to raise an exception when bind is called
    mock_device.bind = AsyncMock(side_effect=Exception("Bind error"))

    # Use a direct patch on the GreeVersatiClient class rather than the import
    with patch(
        "custom_components.gree_versati.config_flow.GreeVersatiClient",
        return_value=mock_client,
    ):
        # Create and initialize the flow
        flow = GreeVersatiConfigFlow()
        flow.hass = hass

        # Call the method being tested
        result = await flow.async_step_bind(
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Device",
            }
        )

        # Verify expectations
        mock_client.run_discovery.assert_called_once()
        assert result is not None
        assert result.get("type") == FlowResultType.ABORT
        assert result.get("reason") == "bind_failed"
