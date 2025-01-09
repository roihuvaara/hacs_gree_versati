from __future__ import annotations

from typing import Any

from greeclimate.awhp_device import AwhpDevice
from greeclimate.base_device import DeviceInfo
from greeclimate.discovery import Discovery, Listener

from .const import LOGGER

class DiscoveryListener(Listener):
    device: AwhpDevice

    def __init__(self, bind):
        """Initialize the event handler."""
        super().__init__()
        self.bind = bind

    """Class to handle incoming device discovery events."""

    async def device_found(self, device_info: DeviceInfo) -> None:
        """A new device was found on the network."""
        if self.bind:
            self.device = AwhpDevice(device_info)
            await self.device.bind()
            await self.device.request_version()
            LOGGER.info(f"Device firmware: {self.device.hid}")

    def get_device(self):
        return self.device
    
class GreeVersatiClient:
    device: AwhpDevice

    
    async def async_get_data(self) -> Any:
        """Fetch data from the device."""
        return self.device.hot_water_temp()

    async def run_discovery(self, bind=False):
        """Run the device discovery process."""
        LOGGER.debug("Scanning network for Gree devices")

        discovery = Discovery()
        listener = DiscoveryListener(bind)
        discovery.add_listener(listener)

        await discovery.scan(wait_for=10)
        LOGGER.info("Done discovering devices")      
        self.device = listener.get_device()

      