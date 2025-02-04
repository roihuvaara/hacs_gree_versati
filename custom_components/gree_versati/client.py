"""Client to interact with the GreeClimate library."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, List

from greeclimate.awhp_device import AwhpDevice
from greeclimate.discovery import Discovery
from .discovery_listener import DiscoveryListener

from .const import LOGGER

if TYPE_CHECKING:
    from greeclimate.base_device import DeviceInfo

LOGGER = logging.getLogger(__name__)

class GreeVersatiClient:
    """Facade class to manage communication with the device."""
    
    def __init__(
        self,
        ip: str | None = None,
        port: int | None = None,
        mac: str | None = None,
        key: str | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.ip = ip
        self.port = port
        self.mac = mac
        self.key = key
        self.device: AwhpDevice | None = None

    async def async_get_data(self) -> any:
        """Fetch data from the device."""
        if self.device is None:
            raise Exception("Device not initialized")
        return self.device.hot_water_temp()

    async def run_discovery(self) -> List[AwhpDevice]:
        """
        Run the device discovery process.

        This method creates a DiscoveryListener, adds it to a Discovery instance,
        waits for the scan to finish, and returns a list containing the discovered device (if any).
        """
        LOGGER.debug("Scanning network for Gree devices")
        discovery = Discovery()
        listener = DiscoveryListener()
        discovery.add_listener(listener)

        await discovery.scan(wait_for=10)  # Wait for 10 seconds (or adjust as needed)
        LOGGER.info("Done discovering devices")
        
        device = listener.get_device()
        if device:
            return [device]
        return []
