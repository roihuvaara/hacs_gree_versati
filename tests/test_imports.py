"""Test importing the greeclimate_versati_fork module."""

import unittest


class TestImports(unittest.TestCase):
    """Test importing required modules."""

    def test_greeclimate_versati_fork(self):
        """Test importing the greeclimate_versati_fork module."""
        import greeclimate_versati_fork

        self.assertIsNotNone(greeclimate_versati_fork)

        # Get module location
        print(f"Found greeclimate_versati_fork at: {greeclimate_versati_fork.__file__}")

    def test_awhp_device(self):
        """Test importing the AwhpDevice and AwhpProps classes."""
        from greeclimate_versati_fork.awhp_device import AwhpDevice, AwhpProps

        self.assertIsNotNone(AwhpDevice)
        self.assertIsNotNone(AwhpProps)

    def test_versati_fork_classes(self):
        """Test importing other classes from greeclimate_versati_fork."""
        from greeclimate_versati_fork.deviceinfo import DeviceInfo
        from greeclimate_versati_fork.discovery import Discovery

        self.assertIsNotNone(DeviceInfo)
        self.assertIsNotNone(Discovery)
