"""Basic tests for the gree_versati integration."""

import unittest
from unittest.mock import MagicMock, patch

from custom_components.gree_versati.client import GreeVersatiClient
from custom_components.gree_versati.const import DOMAIN


class TestGreeVersatiBasics(unittest.TestCase):
    """Test basic functionality of the Gree Versati integration."""

    def setUp(self):
        """Set up test variables."""
        # Test configuration
        self.config = {
            "ip": "192.168.1.100",
            "port": 7000,
            "mac": "AA:BB:CC:DD:EE:FF",
            "key": "test_key",
        }

    def test_domain_constant(self):
        """Test that the domain constant is defined correctly."""
        self.assertEqual(DOMAIN, "gree_versati")

    @patch("gree_versati.awhp_device.AwhpDevice")
    def test_client_initialization(self, mock_device):
        """Test that the client can be initialized."""
        # Configure the mock
        mock_instance = MagicMock()
        mock_device.return_value = mock_instance

        # Create a client with correct parameters
        client = GreeVersatiClient(
            ip=self.config["ip"],
            port=self.config["port"],
            mac=self.config["mac"],
            key=self.config["key"],
        )

        # Test client attributes
        self.assertEqual(client.ip, self.config["ip"])
        self.assertEqual(client.port, self.config["port"])
        self.assertEqual(client.mac, self.config["mac"])
        self.assertEqual(client.key, self.config["key"])

        # Check if device is initially None (not initialized yet)
        self.assertIsNone(client.device)

    def test_import_dependencies(self):
        """Test that all required dependencies can be imported."""
        # Test importing gree_versati
        import gree_versati

        self.assertIsNotNone(gree_versati)

        # Test importing specific classes
        from gree_versati.awhp_device import AwhpDevice, AwhpProps

        self.assertIsNotNone(AwhpDevice)
        self.assertIsNotNone(AwhpProps)
