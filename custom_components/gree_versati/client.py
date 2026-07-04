"""Client to interact with the GreeClimate library."""

from __future__ import annotations

import asyncio
from typing import Any

from .const import (
    COOLING_MODES,
    DEVICE_MODE_TO_MOD,
    HEATING_MODES,
    LOGGER,
)
from .protocol import (
    AwhpDevice,
    AwhpProps,
    DeviceInfo,
    GreeProtocolError,
    search_devices,
)


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
        cipher_type: str | None = None,
    ) -> None:
        """
        Initialize the Gree Versati client.

        Args:
            ip: The IP address of the device
            port: The port number of the device
            mac: The MAC address of the device
            key: The encryption key for the device
            cipher_type: The negotiated cipher scheme ("ecb" or "gcm")

        """
        self.ip = ip
        self.port = port
        self.mac = mac
        self.key = key
        self.cipher_type = cipher_type
        self.device: AwhpDevice | None = None
        self._data: dict[str, Any] = {}  # Add cache for device data
        self._mode_change_lock = asyncio.Lock()

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        if self.device is None:
            LOGGER.error("Device not initialized")
            raise DeviceNotInitializedError

        try:
            LOGGER.debug("Starting data fetch from device")
            # Never poll mid mode-change: the unit power-cycles while
            # switching Mod and would report transitional values
            async with self._mode_change_lock:
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

        With connection parameters (ip, port, mac) a device is created and
        bound: a stored key + cipher type is reused as-is, otherwise a new
        key is negotiated. Without parameters, discovery picks a device.
        """
        LOGGER.debug("Initializing gree versati")

        if self.ip and self.port and self.mac:
            LOGGER.debug(
                "Initializing device with IP: %s, Port: %s, MAC: %s",
                self.ip,
                self.port,
                self.mac,
            )
            device_info = DeviceInfo(self.ip, self.port, self.mac, name=self.mac)
            self.device = AwhpDevice(
                device_info, key=self.key, cipher_type=self.cipher_type
            )

            try:
                await self.device.bind()
            except GreeProtocolError as exc:
                error_msg = f"Binding failed: {exc}"
                raise ConnectionError(error_msg) from exc

            # Reflect what the device negotiated so the config entry can
            # persist it for the next restart.
            self.key = self.device.key
            self.cipher_type = self.device.cipher_type
        else:
            # Optionally, run discovery if connection parameters are not provided.
            devices = await self.run_discovery()
            if devices:
                self.device = devices[0]
            else:
                raise NoDevicesDiscoveredError

    async def run_discovery(self) -> list[AwhpDevice]:
        """Scan the network and return the discovered (unbound) devices."""
        LOGGER.debug("Scanning network for Gree devices")
        infos = await search_devices(wait_for=5)
        LOGGER.info("Done discovering devices, found %d", len(infos))
        return [AwhpDevice(info) for info in infos]

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

        if mode in HEATING_MODES:
            return "heat"
        if mode in COOLING_MODES:
            return "cool"
        # hot-water-only (Mod=2) or unknown: no space heating/cooling
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
        """Set space heating/cooling mode (delegates to set_device_mode)."""
        await self.set_device_mode(mode)

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

    async def set_device_mode(self, mode: str) -> None:
        """
        Set the combined device mode by writing the Mod property.

        The six logical modes map directly to device Mod values (see
        DEVICE_MODE_TO_MOD); hot-water participation is part of Mod, not a
        separate flag. The device only accepts Mod changes while powered
        off (the official app enforces the same OFF -> MODE -> ON
        sequence), so each step is pushed as a separate state update.
        """
        if self.device is None:
            raise DeviceNotInitializedError

        normalized_mode = (mode or "").strip().lower()
        if normalized_mode not in DEVICE_MODE_TO_MOD:
            error_msg = f"Unsupported device mode: {mode}"
            raise ValueError(error_msg)
        target_mod = DEVICE_MODE_TO_MOD[normalized_mode]

        async with self._mode_change_lock:
            current_power = bool(self._data.get("power", False))
            current_mod = self._data.get("mode")

            # Turning off: power off only, leave Mod untouched
            if target_mod is None:
                self.device.set_property(AwhpProps.POWER, value=False)
                await self.device.push_state_update()
                # Optimistic cache update; the unit reports transitional
                # values right after a command, so polling now would lie
                self._data = {**self._data, "power": False}
                return

            if current_mod != target_mod:
                # Power off first (own push, so the OFF reaches the device
                # before the mode change)
                if current_power:
                    self.device.set_property(AwhpProps.POWER, value=False)
                    await self.device.push_state_update()

                self.device.set_property(AwhpProps.MODE, target_mod)
                await self.device.push_state_update()

            self.device.set_property(AwhpProps.POWER, value=True)
            await self.device.push_state_update()
            self._data = {**self._data, "power": True, "mode": target_mod}
