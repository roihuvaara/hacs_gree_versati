"""Client to interact with the GreeClimate library."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from greeclimate.awhp_device import AwhpDevice
from greeclimate.discovery import Discovery, Listener

from .const import LOGGER

if TYPE_CHECKING:
    from greeclimate.base_device import DeviceInfo


class DiscoveryListener(Listener):
    """Handle incoming device discovery events."""

    device: AwhpDevice

    def __init__(self) -> None:
        """Initialize the event handler."""
        super().__init__()
        self.bind = True

    async def device_found(self, device_info: DeviceInfo) -> None:
        """Found a new device on the network."""
        if self.bind:
            self.device = AwhpDevice(device_info)
            await self.device.bind()
            await self.device.request_version()
            LOGGER.info(f"Device firmware: {self.device.hid}")

    def get_device(self) -> AwhpDevice:
        """Get the device that was discovered."""
        return self.device


class GreeVersatiClient:
    """Facade class to manage fetching data from the greeclimate lib."""

    device: AwhpDevice

    async def async_get_data(self) -> Any:
        """Fetch data from the device."""
        return self.device.hot_water_temp()

    async def run_discovery(self) -> None:
        """Run the device discovery process."""
        LOGGER.debug("Scanning network for Gree devices")

        discovery = Discovery()
        listener = DiscoveryListener()
        discovery.add_listener(listener)

        await discovery.scan(wait_for=10)
        LOGGER.info("Done discovering devices")
        self.device = listener.get_device()
