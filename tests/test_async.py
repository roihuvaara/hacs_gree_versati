"""Async tests for the gree_versati integration."""

import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from custom_components.gree_versati.client import GreeVersatiClient


class TestGreeVersatiAsync(unittest.TestCase):
    """Test async functionality of the Gree Versati integration."""

    def setUp(self):
        """Set up test variables."""
        # Test configuration
        self.config = {
            "ip": "192.168.1.100",
            "port": 7000,
            "mac": "AA:BB:CC:DD:EE:FF",
            "key": "test_key",
        }

        # Create an event loop for tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    def test_async_initialize(self):
        """Test that the client can be initialized asynchronously."""
        # Create mocks for the device classes
        mock_device = MagicMock()
        mock_device_info = MagicMock()

        # Configure async bind method that doesn't raise errors
        async def mock_bind(key=None, cipher=None):
            mock_device.key = key
            mock_device.cipher = cipher
            return None

        mock_device.bind = mock_bind

        # Patch both the AwhpDevice class and DeviceInfo class
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=self.config["ip"],
                port=self.config["port"],
                mac=self.config["mac"],
                key=self.config["key"],
                loop=self.loop,
            )

            # Run the initialize method
            self.loop.run_until_complete(client.initialize())

            # Verify device is set
            self.assertEqual(client.device, mock_device)

    def test_async_get_data(self):
        """Test retrieving data from the device."""
        # Create mock device
        mock_device = MagicMock()
        mock_device_info = MagicMock()

        # Configure async methods
        async def mock_bind(key=None, cipher=None):
            return None

        async def mock_get_properties():
            return {
                "pow": 1,  # Power on
                "mode": 4,  # Heat mode
            }

        mock_device.bind = mock_bind
        mock_device.get_all_properties = mock_get_properties

        # Setup temperature helper methods
        mock_device.t_water_out_pe = MagicMock(return_value=45.5)
        mock_device.t_water_in_pe = MagicMock(return_value=40.0)
        mock_device.hot_water_temp = MagicMock(return_value=50.0)
        mock_device.t_opt_water = MagicMock(return_value=48.0)

        # Patch both the AwhpDevice class and DeviceInfo class
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=self.config["ip"],
                port=self.config["port"],
                mac=self.config["mac"],
                key=self.config["key"],
                loop=self.loop,
            )

            # Initialize client
            self.loop.run_until_complete(client.initialize())

            # Get data
            data = self.loop.run_until_complete(client.async_get_data())

            # Verify data
            self.assertEqual(data["water_out_temp"], 45.5)
            self.assertEqual(data["water_in_temp"], 40.0)
            self.assertEqual(data["hot_water_temp"], 50.0)
            self.assertEqual(data["opt_water_temp"], 48.0)
