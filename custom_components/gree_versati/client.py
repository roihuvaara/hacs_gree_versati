"""Client to interact with the GreeClimate library."""

from __future__ import annotations

import asyncio
from typing import Any

from greeclimate_versati_fork.awhp_device import AwhpDevice, AwhpProps
from greeclimate_versati_fork.deviceinfo import DeviceInfo
from greeclimate_versati_fork.discovery import Discovery

from .const import COOL_MODE, HEAT_MODE, LOGGER
from .discovery_listener import DiscoveryListener

# Define constants for HVAC mode values are now in const.py


class DeviceNotInitializedError(RuntimeError):
    """Error raised when device is not initialized."""

    def __init__(self) -> None:
        """Initialize with a default message."""
        super().__init__("Device not initialized")


class NoDevicesDiscoveredError(ConnectionError):
    """Error raised when no devices are discovered."""

    def __init__(self) -> None:
        """Initialize with a default message."""
        super().__init__("No devices discovered")


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
        """
        Initialize the Gree Versati client.

        Args:
            ip: The IP address of the device
            port: The port number of the device
            mac: The MAC address of the device
            key: The encryption key for the device
            loop: The event loop to use

        """
        self.loop = loop or asyncio.get_event_loop()
        self.ip = ip
        self.port = port
        self.mac = mac
        self.key = key
        self.device: AwhpDevice | None = None
        self._data: dict[str, Any] = {}  # Add cache for device data

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        if self.device is None:
            LOGGER.error("Device not initialized")
            raise DeviceNotInitializedError

        try:
            LOGGER.debug("Starting data fetch from device")
            raw_data = await self.device.get_all_properties()
            LOGGER.debug("Raw data from device: %s", raw_data)

            # Add debug logging for each temperature calculation
            water_out_temp = self.device.t_water_out_pe(raw_data)
            LOGGER.debug("Water out temp: %s", water_out_temp)

            water_in_temp = self.device.t_water_in_pe(raw_data)
            LOGGER.debug("Water in temp: %s", water_in_temp)

            hot_water_temp = self.device.hot_water_temp(raw_data)
            LOGGER.debug("Hot water temp: %s", hot_water_temp)

            opt_water_temp = self.device.t_opt_water(raw_data)
            LOGGER.debug("Optimal water temp: %s", opt_water_temp)

            self._data = {
                # Current temperatures using helper methods with raw data
                "water_out_temp": water_out_temp,
                "water_in_temp": water_in_temp,
                "hot_water_temp": hot_water_temp,
                "opt_water_temp": opt_water_temp,
                # Target temperatures (these are already in correct format)
                "heat_temp_set": raw_data.get(AwhpProps.HEAT_TEMP_SET.value),
                "cool_temp_set": raw_data.get(AwhpProps.COOL_TEMP_SET.value),
                "hot_water_temp_set": raw_data.get(AwhpProps.HOT_WATER_TEMP_SET.value),
                # Operation modes and states
                "power": raw_data.get(AwhpProps.POWER.value),
                "mode": raw_data.get(AwhpProps.MODE.value),
                "fast_heat_water": raw_data.get(AwhpProps.FAST_HEAT_WATER.value),
                # Status indicators
                "tank_heater_status": raw_data.get(AwhpProps.TANK_HEATER_STATUS.value),
                "defrosting_status": raw_data.get(
                    AwhpProps.SYSTEM_DEFROSTING_STATUS.value
                ),
                "hp_heater_1_status": raw_data.get(AwhpProps.HP_HEATER_1_STATUS.value),
                "hp_heater_2_status": raw_data.get(AwhpProps.HP_HEATER_2_STATUS.value),
                "frost_protection": raw_data.get(
                    AwhpProps.AUTOMATIC_FROST_PROTECTION.value
                ),
                # Device information
                "versati_series": raw_data.get(AwhpProps.VERSATI_SERIES.value),
            }

            LOGGER.debug("Processed data: %s", self._data)
            return self._data

        except Exception as exc:
            LOGGER.exception("Failed to fetch device data")
            error_msg = f"Failed to fetch device data: {exc}"
            raise RuntimeError(error_msg) from exc

    async def initialize(self) -> None:
        """
        Initialize the device connection.

        If the connection parameters (ip, port, mac) are provided, create a DeviceInfo
        and then an AwhpDevice. Then, bind to the device using the stored key if
        provided.
        """
        LOGGER.debug("Initializing gree versati")

        if self.ip and self.port and self.mac:
            LOGGER.debug(
                "Initializing device with IP: %s, Port: %s, MAC: %s",
                self.ip,
                self.port,
                self.mac,
            )
            # Create the device info from stored parameters.
            device_info = DeviceInfo(self.ip, self.port, self.mac, name=self.mac)
            self.device = AwhpDevice(device_info)

            try:
                if self.key:
                    # Use the provided key to bind.
                    self.device.device_key = self.key
                    LOGGER.debug("Re-binding with existing key")
                    await self.device.bind(key=self.key)
                else:
                    # Bind without a key, letting the device negotiate one.
                    await self.device.bind()
            except Exception as exc:
                # Handle binding errors as needed.
                error_msg = f"Binding failed: {exc}"
                raise ConnectionError(error_msg) from exc
        else:
            # Optionally, run discovery if connection parameters are not provided.
            devices = await self.run_discovery()
            if devices:
                self.device = devices[0]
            else:
                raise NoDevicesDiscoveredError

    async def run_discovery(self) -> list[AwhpDevice]:
        """
        Run network discovery to find Gree devices.

        This method creates a DiscoveryListener, adds it to a Discovery instance,
        waits for the scan to finish, and returns a list containing the
        discovered device (if any).
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
    def current_temperature(self) -> float | None:
        """Get the current water temperature."""
        return self._data.get("water_out_temp")

    @property
    def target_temperature(self) -> float | None:
        """Get the target temperature based on current mode."""
        if self.hvac_mode == "heat":
            return self._data.get("heat_temp_set")
        if self.hvac_mode == "cool":
            return self._data.get("cool_temp_set")
        return None

    @property
    def hvac_mode(self) -> str:
        """Get the current HVAC mode."""
        mode = self._data.get("mode")

        if mode == HEAT_MODE:  # Heat mode
            return "heat"
        if mode == COOL_MODE:  # Cool mode
            return "cool"
        return "off"

    @property
    def is_on(self) -> bool:
        """Return true if the device is on."""
        return bool(self._data.get("power", False))

    @property
    def dhw_temperature(self) -> float | None:
        """Get the current domestic hot water temperature."""
        return self._data.get("hot_water_temp")

    @property
    def dhw_target_temperature(self) -> float | None:
        """Get the target domestic hot water temperature."""
        return self._data.get("hot_water_temp_set")

    @property
    def dhw_mode(self) -> str:
        """Get the current DHW mode."""
        return "performance" if self._data.get("fast_heat_water") else "normal"

    async def set_temperature(
        self, temperature: float, mode: str | None = None
    ) -> None:
        """Set the target temperature."""
        if self.device is None:
            raise DeviceNotInitializedError

        if mode == "heat" or (mode is None and self.hvac_mode == "heat"):
            self.device.set_property(AwhpProps.HEAT_TEMP_SET, int(temperature))
        elif mode == "cool" or (mode is None and self.hvac_mode == "cool"):
            self.device.set_property(AwhpProps.COOL_TEMP_SET, int(temperature))

        await self.device.push_state_update()
        await self.async_get_data()

    async def set_dhw_temperature(self, temperature: float) -> None:
        """Set the target DHW temperature."""
        if self.device is None:
            raise DeviceNotInitializedError

        self.device.set_property(AwhpProps.HOT_WATER_TEMP_SET, int(temperature))
        await self.device.push_state_update()
        await self.async_get_data()

    async def set_hvac_mode(self, mode: str) -> None:
        """Set the HVAC mode."""
        if self.device is None:
            raise DeviceNotInitializedError

        if mode == "heat":
            self.device.set_property(AwhpProps.MODE, HEAT_MODE)
            self.device.set_property(AwhpProps.POWER, value=True)
        elif mode == "cool":
            self.device.set_property(AwhpProps.MODE, COOL_MODE)
            self.device.set_property(AwhpProps.POWER, value=True)
        elif mode == "off":
            self.device.set_property(AwhpProps.POWER, value=False)

        await self.device.push_state_update()
        await self.async_get_data()

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the DHW mode."""
        if self.device is None:
            raise DeviceNotInitializedError

        if mode == "performance":
            self.device.set_property(AwhpProps.FAST_HEAT_WATER, value=True)
        elif mode == "normal":
            self.device.set_property(AwhpProps.FAST_HEAT_WATER, value=False)

        await self.device.push_state_update()
        await self.async_get_data()
