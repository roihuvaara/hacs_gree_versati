"""Listener for discovering Gree Versati devices on the network."""

import logging

from gree_versati.awhp_device import AwhpDevice
from gree_versati.deviceinfo import DeviceInfo
from gree_versati.discovery import Listener

LOGGER = logging.getLogger(__name__)


class DiscoveryListener(Listener):
    """Handle incoming device discovery events."""

    def __init__(self) -> None:
        """Initialize the event handler."""
        super().__init__()
        self.bind = True
        self.device: AwhpDevice | None = None

    async def device_found(self, device_info: DeviceInfo) -> None:
        """Handle new device discovered on the network."""
        if self.bind and self.device is None:
            # Create a device instance from the discovered info.
            self.device = AwhpDevice(device_info)
            try:
                # Bind to the device to negotiate its key.
                await self.device.bind()
                # Optionally request additional information like firmware version.
                await self.device.request_version()
                LOGGER.info("Device firmware: %s", self.device.hid)
            except Exception:
                LOGGER.exception("Failed to bind discovered device")
                self.device = None

    def get_device(self) -> AwhpDevice | None:
        """Return the discovered (and bound) device, if any."""
        return self.device
