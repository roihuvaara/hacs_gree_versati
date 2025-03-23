"""Tests for an enhanced discovery listener that can handle multiple devices."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from gree_versati.deviceinfo import DeviceInfo

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
def mock_device_info_2():
    """Create a second mock device info."""
    device_info = MagicMock(spec=DeviceInfo)
    device_info.ip = "192.168.1.101"
    device_info.port = 7000
    device_info.mac = "11:22:33:44:55:66"
    device_info.name = "Test Device 2"
    return device_info


class TestEnhancedDiscoveryListener:
    """Tests for an enhanced discovery listener that can handle multiple devices."""

    @pytest.mark.asyncio
    async def test_device_found_single_device(self, mock_device_info):
        """Test finding a single device."""
        # Mock AwhpDevice to return our mock device
        with patch(
            "custom_components.gree_versati.discovery_listener.AwhpDevice"
        ) as mock_awhp:
            # Configure the mock to return a device that can be successfully bound
            mock_device = MagicMock()
            mock_device.bind = AsyncMock()
            mock_device.request_version = AsyncMock()
            mock_device.hid = "TestHID123"
            mock_device.device_info = mock_device_info
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
    async def test_enhanced_listener_multiple_devices(
        self,
        mock_device_info,
        mock_device_info_2,
    ):
        """Test an enhanced listener that can handle multiple devices."""
        # Create a mock for AwhpDevice
        mock_device_1 = MagicMock()
        mock_device_1.bind = AsyncMock()
        mock_device_1.request_version = AsyncMock()
        mock_device_1.hid = "TestHID123"
        mock_device_1.device_info = mock_device_info

        mock_device_2 = MagicMock()
        mock_device_2.bind = AsyncMock()
        mock_device_2.request_version = AsyncMock()
        mock_device_2.hid = "TestHID456"
        mock_device_2.device_info = mock_device_info_2

        # Create an enhanced version of the DiscoveryListener
        class EnhancedDiscoveryListener(DiscoveryListener):
            """Enhanced discovery listener that can handle multiple devices."""

            def __init__(self) -> None:
                """Initialize the event handler."""
                super().__init__()
                self.devices = []

                # Override the device creation to use our mocks
                self._create_device = self._mock_create_device

            def _mock_create_device(self, device_info):
                """Mock device creation to return our pre-configured mocks."""
                if device_info.mac == "AA:BB:CC:DD:EE:FF":
                    return mock_device_1
                return mock_device_2

            async def device_found(self, device_info: DeviceInfo) -> None:
                """Called when a new device is found on the network."""
                # Create a device instance from the discovered info
                device = self._create_device(device_info)
                try:
                    # Bind to the device to negotiate its key
                    await device.bind()
                    # Optionally request additional information
                    await device.request_version()
                    # Store the device
                    self.devices.append(device)
                    # Also set the first device as the primary device for backward compatibility
                    if not self.device:
                        self.device = device
                except Exception:
                    # Log the error but continue with other devices
                    pass

            def get_devices(self) -> list:
                """Return all discovered and bound devices."""
                return self.devices

        # Create a listener and simulate device discovery
        listener = EnhancedDiscoveryListener()

        # Discover the first device
        await listener.device_found(mock_device_info)

        # Verify bind was called for the first device
        mock_device_1.bind.assert_called_once()

        # Verify request_version was called for the first device
        mock_device_1.request_version.assert_called_once()

        # Verify the first device was stored
        assert listener.device == mock_device_1
        assert len(listener.devices) == 1
        assert listener.devices[0] == mock_device_1

        # Discover the second device
        await listener.device_found(mock_device_info_2)

        # Verify bind was called for the second device
        mock_device_2.bind.assert_called_once()

        # Verify request_version was called for the second device
        mock_device_2.request_version.assert_called_once()

        # Verify both devices were stored
        assert listener.device == mock_device_1  # First device remains the primary
        assert len(listener.devices) == 2
        assert listener.devices[0] == mock_device_1
        assert listener.devices[1] == mock_device_2

        # Verify get_devices returns all devices
        assert listener.get_devices() == [mock_device_1, mock_device_2]

    @pytest.mark.asyncio
    async def test_enhanced_listener_binding_failure(
        self,
        mock_device_info,
        mock_device_info_2,
    ):
        """Test an enhanced listener when binding fails for one device."""
        # Create a mock for AwhpDevice
        mock_device_1 = MagicMock()
        mock_device_1.bind = AsyncMock(side_effect=Exception("Binding failed"))
        mock_device_1.device_info = mock_device_info

        mock_device_2 = MagicMock()
        mock_device_2.bind = AsyncMock()
        mock_device_2.request_version = AsyncMock()
        mock_device_2.hid = "TestHID456"
        mock_device_2.device_info = mock_device_info_2

        # Create an enhanced version of the DiscoveryListener
        class EnhancedDiscoveryListener(DiscoveryListener):
            """Enhanced discovery listener that can handle multiple devices."""

            def __init__(self) -> None:
                """Initialize the event handler."""
                super().__init__()
                self.devices = []

                # Override the device creation to use our mocks
                self._create_device = self._mock_create_device

            def _mock_create_device(self, device_info):
                """Mock device creation to return our pre-configured mocks."""
                if device_info.mac == "AA:BB:CC:DD:EE:FF":
                    return mock_device_1
                return mock_device_2

            async def device_found(self, device_info: DeviceInfo) -> None:
                """Called when a new device is found on the network."""
                # Create a device instance from the discovered info
                device = self._create_device(device_info)
                try:
                    # Bind to the device to negotiate its key
                    await device.bind()
                    # Optionally request additional information
                    await device.request_version()
                    # Store the device
                    self.devices.append(device)
                    # Also set the first device as the primary device for backward compatibility
                    if not self.device:
                        self.device = device
                except Exception:
                    # Log the error but continue with other devices
                    pass

            def get_devices(self) -> list:
                """Return all discovered and bound devices."""
                return self.devices

        # Create a listener and simulate device discovery
        listener = EnhancedDiscoveryListener()

        # Discover the first device (which will fail to bind)
        await listener.device_found(mock_device_info)

        # Verify bind was called for the first device
        mock_device_1.bind.assert_called_once()

        # Verify the first device was not stored due to binding failure
        assert listener.device is None
        assert len(listener.devices) == 0

        # Discover the second device (which will bind successfully)
        await listener.device_found(mock_device_info_2)

        # Verify bind was called for the second device
        mock_device_2.bind.assert_called_once()

        # Verify request_version was called for the second device
        mock_device_2.request_version.assert_called_once()

        # Verify only the second device was stored
        assert listener.device == mock_device_2
        assert len(listener.devices) == 1
        assert listener.devices[0] == mock_device_2

        # Verify get_devices returns only the second device
        assert listener.get_devices() == [mock_device_2]
