import logging

from greeclimate_versati_fork.awhp_device import AwhpDevice
from greeclimate_versati_fork.deviceinfo import DeviceInfo
from greeclimate_versati_fork.discovery import Listener

LOGGER = logging.getLogger(__name__)


class DiscoveryListener(Listener):
    """Handle incoming device discovery events."""

    def __init__(self) -> None:
        """Initialize the event handler."""
        super().__init__()
        self.bind = True
        self.device: AwhpDevice | None = None

    async def device_found(self, device_info: DeviceInfo) -> None:
        """Called when a new device is found on the network."""
        if self.bind and self.device is None:
            # Create a device instance from the discovered info.
            self.device = AwhpDevice(device_info)
            try:
                # Bind to the device to negotiate its key.
                await self.device.bind()
                # Optionally request additional information like firmware version.
                await self.device.request_version()
                LOGGER.info(f"Device firmware: {self.device.hid}")
            except Exception as exc:
                LOGGER.error("Failed to bind discovered device: %s", exc)
                self.device = None

    def get_device(self) -> AwhpDevice | None:
        """Return the discovered (and bound) device, if any."""
        return self.device
