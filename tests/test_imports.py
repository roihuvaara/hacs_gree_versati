"""Test importing the vendored protocol package."""

import unittest


class TestImports(unittest.TestCase):
    """Test importing the vendored protocol package."""

    def test_protocol_package(self):
        """Test importing the protocol package."""
        from custom_components.gree_versati import protocol

        self.assertIsNotNone(protocol)

        from custom_components.gree_versati.protocol import AwhpDevice, AwhpProps

        self.assertIsNotNone(AwhpDevice)
        self.assertIsNotNone(AwhpProps)

    def test_other_classes(self):
        """Test importing supporting classes from the protocol package."""
        from custom_components.gree_versati.protocol import (
            DeviceInfo,
            search_devices,
        )

        self.assertIsNotNone(DeviceInfo)
        self.assertIsNotNone(search_devices)
