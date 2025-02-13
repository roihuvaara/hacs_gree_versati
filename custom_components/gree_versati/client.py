"""Client to interact with the GreeClimate library."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, List

from greeclimate_versati_fork.awhp_device import AwhpDevice
from greeclimate_versati_fork.discovery import Discovery
from greeclimate_versati_fork.deviceinfo import DeviceInfo
from .discovery_listener import DiscoveryListener
from greeclimate_versati_fork.awhp_device import AwhpProps

from .const import LOGGER

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
        self._data = {}  # Add cache for device data

    async def async_get_data(self) -> dict:
        """Fetch data from the device."""
        if self.device is None:
            raise Exception("Device not initialized")
        
        try:
            # Get all properties in one request
            raw_data = await self.device.get_all_properties()
            
            # Transform the raw data into our desired format
            self._data = {
                # Current temperatures using helper methods with raw data
                "water_out_temp": self.device.t_water_out_pe(raw_data),
                "water_in_temp": self.device.t_water_in_pe(raw_data),
                "hot_water_temp": self.device.hot_water_temp(raw_data),
                "opt_water_temp": self.device.t_opt_water(raw_data),
                "remote_home_temp": self.device.remote_home_temp(raw_data),
                
                # Target temperatures (these are already in correct format)
                "heat_temp_set": raw_data[AwhpProps.HEAT_TEMP_SET.value],
                "cool_temp_set": raw_data[AwhpProps.COOL_TEMP_SET.value],
                "hot_water_temp_set": raw_data[AwhpProps.HOT_WATER_TEMP_SET.value],
                
                # Operation modes and states
                "power": raw_data[AwhpProps.POWER.value],
                "mode": raw_data[AwhpProps.MODE.value],
                "fast_heat_water": raw_data[AwhpProps.FAST_HEAT_WATER.value],
                
                # Status indicators
                "tank_heater_status": raw_data[AwhpProps.TANK_HEATER_STATUS.value],
                "defrosting_status": raw_data[AwhpProps.SYSTEM_DEFROSTING_STATUS.value],
                "hp_heater_1_status": raw_data[AwhpProps.HP_HEATER_1_STATUS.value],
                "hp_heater_2_status": raw_data[AwhpProps.HP_HEATER_2_STATUS.value],
                "frost_protection": raw_data[AwhpProps.AUTOMATIC_FROST_PROTECTION.value],
            }
            return self._data
            
        except Exception as exc:
            raise Exception(f"Failed to fetch device data: {exc}")

    async def initialize(self) -> None:
        """
        Initialize the device connection.

        If the connection parameters (ip, port, mac) are provided, create a DeviceInfo
        and then an AwhpDevice. Then, bind to the device using the stored key if provided.
        """
        if self.ip and self.port and self.mac:
            # Create the device info from stored parameters.
            device_info = DeviceInfo(self.ip, self.port, self.mac, name=self.mac)
            self.device = AwhpDevice(device_info)
            try:
                if self.key:
                    await self.device.bind(key=self.key)
                else:
                    # Bind without a key, letting the device negotiate one.
                    await self.device.bind()
            except Exception as exc:
                # Handle binding errors as needed.
                raise Exception(f"Binding failed: {exc}")
        else:
            # Optionally, run discovery if connection parameters are not provided.
            devices = await self.run_discovery()
            if devices:
                self.device = devices[0]
            else:
                raise Exception("No devices discovered.")

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

    @property
    def current_temperature(self) -> float:
        """Get the current water temperature."""
        return self._data.get("water_out_temp")

    @property
    def target_temperature(self) -> float:
        """Get the target temperature based on current mode."""
        if self.hvac_mode == "heat":
            return self._data.get("heat_temp_set")
        elif self.hvac_mode == "cool":
            return self._data.get("cool_temp_set")
        return None

    @property
    def hvac_mode(self) -> str:
        """Get the current HVAC mode."""
        mode = self._data.get("mode")
        if mode == 4:  # Heat mode
            return "heat"
        elif mode == 1:  # Cool mode
            return "cool"
        return "off"

    @property
    def is_on(self) -> bool:
        """Return true if the device is on."""
        return self._data.get("power", False)

    @property
    def dhw_temperature(self) -> float:
        """Get the current domestic hot water temperature."""
        return self._data.get("hot_water_temp")

    @property
    def dhw_target_temperature(self) -> float:
        """Get the target domestic hot water temperature."""
        return self._data.get("hot_water_temp_set")

    @property
    def dhw_mode(self) -> str:
        """Get the current DHW mode."""
        return "performance" if self._data.get("fast_heat_water") else "normal"

    async def set_temperature(self, temperature: float, mode: str = None) -> None:
        """Set the target temperature."""
        if mode == "heat" or (mode is None and self.hvac_mode == "heat"):
            self.device.heat_temp_set = int(temperature)
        elif mode == "cool" or (mode is None and self.hvac_mode == "cool"):
            self.device.cool_temp_set = int(temperature)
        # Optionally refresh data after setting
        await self.async_get_data()

    async def set_dhw_temperature(self, temperature: float) -> None:
        """Set the target DHW temperature."""
        self.device.hot_water_temp_set = int(temperature)

    async def set_hvac_mode(self, mode: str) -> None:
        """Set the HVAC mode."""
        if mode == "heat":
            self.device.mode = 4
        elif mode == "cool":
            self.device.mode = 1
        elif mode == "off":
            self.device.power = False

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the DHW mode."""
        if mode == "performance":
            self.device.fast_heat_water = True
        elif mode == "normal":
            self.device.fast_heat_water = False
