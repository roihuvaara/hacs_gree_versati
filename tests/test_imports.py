"""Test importing the gree_versati module."""

import unittest


class TestImports(unittest.TestCase):
    """Test importing the gree_versati module."""

    def test_gree_versati(self):
        """Test importing the gree_versati module."""
        import gree_versati

        self.assertIsNotNone(gree_versati)
        print(f"Found gree_versati at: {gree_versati.__file__}")

        # Test importing specific classes
        from gree_versati.awhp_device import AwhpDevice, AwhpProps

        self.assertIsNotNone(AwhpDevice)
        self.assertIsNotNone(AwhpProps)

    def test_other_classes(self):
        """Test importing other classes from gree_versati."""
        from gree_versati.deviceinfo import DeviceInfo
        from gree_versati.discovery import Discovery

        self.assertIsNotNone(DeviceInfo)
        self.assertIsNotNone(Discovery)
