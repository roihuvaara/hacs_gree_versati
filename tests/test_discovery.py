"""Tests for client-level device discovery."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.gree_versati.client import GreeVersatiClient
from custom_components.gree_versati.protocol import DeviceInfo


@pytest.fixture
def mock_device():
    """Create a mock bound device."""
    device = MagicMock()
    device.device_info = DeviceInfo(
        ip="192.168.1.123", port=7000, mac="aabbccddeeff", name="Test Device"
    )
    return device


class TestClientDiscovery:
    """Tests for the discovery functionality in the GreeVersatiClient class."""

    @pytest.mark.asyncio
    async def test_run_discovery_success(self):
        """Test successful device discovery."""
        info = DeviceInfo(
            ip="192.168.1.123", port=7000, mac="aabbccddeeff", name="Test Device"
        )
        with patch(
            "custom_components.gree_versati.client.search_devices",
            new=AsyncMock(return_value=[info]),
        ) as mock_search:
            client = GreeVersatiClient()
            devices = await client.run_discovery()

            mock_search.assert_awaited_once()
            assert len(devices) == 1
            assert devices[0].device_info == info
            # Discovered devices are not yet bound
            assert devices[0].key is None

    @pytest.mark.asyncio
    async def test_run_discovery_no_devices(self):
        """Test device discovery when no devices are found."""
        with patch(
            "custom_components.gree_versati.client.search_devices",
            new=AsyncMock(return_value=[]),
        ):
            client = GreeVersatiClient()
            devices = await client.run_discovery()

            assert devices == []

    @pytest.mark.asyncio
    async def test_run_discovery_exception(self):
        """Test device discovery when an exception occurs."""
        with patch(
            "custom_components.gree_versati.client.search_devices",
            new=AsyncMock(side_effect=Exception("Network error")),
        ):
            client = GreeVersatiClient()

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
