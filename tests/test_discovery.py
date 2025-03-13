"""Tests for the device discovery functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from greeclimate_versati_fork.awhp_device import AwhpDevice
from greeclimate_versati_fork.deviceinfo import DeviceInfo

from custom_components.gree_versati.client import GreeVersatiClient
from custom_components.gree_versati.discovery_listener import DiscoveryListener


@pytest.fixture
def mock_device_info():
    """Create a mock device info."""
    device_info = MagicMock(spec=DeviceInfo)
    device_info.ip = "192.168.1.100"
    device_info.port = 7000
    device_info.mac = "AA:BB:CC:DD:EE:FF"
    device_info.name = "Test Device"
    return device_info


@pytest.fixture
def mock_device(mock_device_info):
    """Create a mock device."""
    device = MagicMock(spec=AwhpDevice)
    device.device_info = mock_device_info
    device.bind = AsyncMock()
    device.request_version = AsyncMock()
    device.ip = mock_device_info.ip
    device.name = "Test Device"
    device.hid = "TestHID123"
    return device


class TestDiscoveryListener:
    """Tests for the DiscoveryListener class."""

    @pytest.mark.asyncio
    async def test_device_found_success(self, mock_device_info):
        """Test successful device discovery and binding."""
        # Mock AwhpDevice to return our mock device
        with patch(
            "custom_components.gree_versati.discovery_listener.AwhpDevice"
        ) as mock_awhp:
            # Configure the mock to return a device that can be successfully bound
            mock_device = MagicMock()
            mock_device.bind = AsyncMock()
            mock_device.request_version = AsyncMock()
            mock_device.hid = "TestHID123"
            mock_awhp.return_value = mock_device

            # Create a listener and simulate device discovery
            listener = DiscoveryListener()
            await listener.device_found(mock_device_info)

            # Verify the device was created with the correct info
            mock_awhp.assert_called_once_with(mock_device_info)

            # Verify bind was called
            mock_device.bind.assert_called_once()

            # Verify request_version was called
            mock_device.request_version.assert_called_once()

            # Verify the device was stored
            assert listener.device == mock_device

    @pytest.mark.asyncio
    async def test_device_found_bind_failure(self, mock_device_info):
        """Test device discovery with binding failure."""
        # Mock AwhpDevice to return our mock device
        with patch(
            "custom_components.gree_versati.discovery_listener.AwhpDevice"
        ) as mock_awhp:
            # Configure the mock to fail during binding
            mock_device = MagicMock()
            mock_device.bind = AsyncMock(side_effect=Exception("Binding failed"))
            mock_awhp.return_value = mock_device

            # Create a listener and simulate device discovery
            listener = DiscoveryListener()
            await listener.device_found(mock_device_info)

            # Verify the device was created with the correct info
            mock_awhp.assert_called_once_with(mock_device_info)

            # Verify bind was called
            mock_device.bind.assert_called_once()

            # Verify the device was not stored due to binding failure
            assert listener.device is None

    @pytest.mark.asyncio
    async def test_device_found_already_bound(self, mock_device_info):
        """Test device discovery when a device is already bound."""
        # Create a listener with a pre-existing device
        listener = DiscoveryListener()
        listener.device = MagicMock()

        # Simulate device discovery
        await listener.device_found(mock_device_info)

        # Verify the original device was not replaced
        assert listener.device is not None
        assert isinstance(listener.device, MagicMock)

    def test_get_device(self):
        """Test the get_device method."""
        # Create a listener with a device
        listener = DiscoveryListener()
        mock_device = MagicMock()
        listener.device = mock_device

        # Verify get_device returns the device
        assert listener.get_device() == mock_device

        # Create a listener without a device
        listener = DiscoveryListener()

        # Verify get_device returns None
        assert listener.get_device() is None


class TestClientDiscovery:
    """Tests for the discovery functionality in the GreeVersatiClient class."""

    @pytest.mark.asyncio
    async def test_run_discovery_success(self, mock_device):
        """Test successful device discovery."""
        # Mock Discovery and DiscoveryListener
        with (
            patch(
                "custom_components.gree_versati.client.Discovery"
            ) as mock_discovery_cls,
            patch(
                "custom_components.gree_versati.client.DiscoveryListener"
            ) as mock_listener_cls,
        ):
            # Configure the mocks
            mock_discovery = MagicMock()
            mock_discovery.scan = AsyncMock()
            mock_discovery_cls.return_value = mock_discovery

            mock_listener = MagicMock()
            mock_listener.get_device.return_value = mock_device
            mock_listener_cls.return_value = mock_listener

            # Create a client and run discovery
            client = GreeVersatiClient()
            devices = await client.run_discovery()

            # Verify Discovery was created
            mock_discovery_cls.assert_called_once()

            # Verify DiscoveryListener was created
            mock_listener_cls.assert_called_once()

            # Verify the listener was added to the discovery
            mock_discovery.add_listener.assert_called_once_with(mock_listener)

            # Verify scan was called
            mock_discovery.scan.assert_called_once()

            # Verify get_device was called
            mock_listener.get_device.assert_called_once()

            # Verify the correct device was returned
            assert len(devices) == 1
            assert devices[0] == mock_device

    @pytest.mark.asyncio
    async def test_run_discovery_no_devices(self):
        """Test device discovery when no devices are found."""
        # Mock Discovery and DiscoveryListener
        with (
            patch(
                "custom_components.gree_versati.client.Discovery"
            ) as mock_discovery_cls,
            patch(
                "custom_components.gree_versati.client.DiscoveryListener"
            ) as mock_listener_cls,
        ):
            # Configure the mocks
            mock_discovery = MagicMock()
            mock_discovery.scan = AsyncMock()
            mock_discovery_cls.return_value = mock_discovery

            mock_listener = MagicMock()
            mock_listener.get_device.return_value = None
            mock_listener_cls.return_value = mock_listener

            # Create a client and run discovery
            client = GreeVersatiClient()
            devices = await client.run_discovery()

            # Verify the correct empty list was returned
            assert devices == []

    @pytest.mark.asyncio
    async def test_run_discovery_exception(self):
        """Test device discovery when an exception occurs."""
        # Mock Discovery to raise an exception
        with patch(
            "custom_components.gree_versati.client.Discovery"
        ) as mock_discovery_cls:
            # Configure the mock to raise an exception
            mock_discovery = MagicMock()
            mock_discovery.scan = AsyncMock(side_effect=Exception("Network error"))
            mock_discovery_cls.return_value = mock_discovery

            # Create a client and run discovery
            client = GreeVersatiClient()

            # Verify the exception is propagated
            with pytest.raises(Exception, match="Network error"):
                await client.run_discovery()

    @pytest.mark.asyncio
    async def test_initialize_with_discovery(self, mock_device):
        """Test initialize method using discovery."""
        # Create a client with no connection parameters
        client = GreeVersatiClient()

        # Mock run_discovery to return a device
        client.run_discovery = AsyncMock(return_value=[mock_device])

        # Initialize client
        await client.initialize()

        # Verify run_discovery was called
        client.run_discovery.assert_called_once()

        # Verify device is set
        assert client.device == mock_device

    @pytest.mark.asyncio
    async def test_initialize_with_discovery_no_devices(self):
        """Test initialize method using discovery when no devices are found."""
        # Create a client with no connection parameters
        client = GreeVersatiClient()

        # Mock run_discovery to return no devices
        client.run_discovery = AsyncMock(return_value=[])

        # Verify initialize raises an exception
        with pytest.raises(Exception, match="No devices discovered"):
            await client.initialize()

    @pytest.mark.asyncio
    async def test_initialize_with_discovery_exception(self):
        """Test initialize method when discovery raises an exception."""
        # Create a client with no connection parameters
        client = GreeVersatiClient()

        # Mock run_discovery to raise an exception
        client.run_discovery = AsyncMock(side_effect=Exception("Network error"))

        # Verify initialize propagates the exception
        with pytest.raises(Exception, match="Network error"):
            await client.initialize()
