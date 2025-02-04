"""Water Heater entity for the Gree Versati integration."""
from __future__ import annotations
import logging

from homeassistant.components.water_heater import WaterHeaterEntity, SUPPORT_TARGET_TEMPERATURE
from homeassistant.const import TEMP_CELSIUS, STATE_OFF, STATE_ON
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GreeVersatiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the Gree Versati water heater platform from a config entry."""
    coordinator: GreeVersatiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([GreeVersatiWaterHeater(coordinator, entry)], True)


class GreeVersatiWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Representation of the Gree Versati Water Heater entity."""

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.data.get("name", "Gree Versati Water Heater")
        self._attr_unique_id = f"{entry.data.get('mac')}_waterheater"
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        self._attr_temperature_unit = TEMP_CELSIUS
        self._target_temperature: float | None = None

    @property
    def current_temperature(self) -> float | None:
        """Return the current water temperature.

        This example assumes that the coordinator's data is either a float
        representing the temperature or a dict with a key 'hot_water_temp'.
        Adjust as needed.
        """
        if isinstance(self.coordinator.data, dict):
            return self.coordinator.data.get("hot_water_temp")
        return self.coordinator.data

    @property
    def target_temperature(self) -> float | None:
        """Return the target water temperature."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set a new target temperature for the water heater."""
        new_temp = kwargs.get("temperature")
        if new_temp is None:
            return
        # Here you would call your device API to update the water heater's target temperature.
        self._target_temperature = new_temp
        _LOGGER.debug("Setting water heater target temperature to %s", new_temp)
        self.async_write_ha_state()

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode.

        In this example, if a target temperature is set, the water heater is 'on',
        otherwise it's 'off'.
        """
        return STATE_ON if self._target_temperature is not None else STATE_OFF

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set the HVAC mode for the water heater."""
        if hvac_mode == STATE_OFF:
            self._target_temperature = None
            _LOGGER.debug("Water heater turned off.")
        else:
            if self._target_temperature is None:
                self._target_temperature = 50.0  # default target temperature
            _LOGGER.debug("Water heater turned on. Target temperature: %s", self._target_temperature)
        self.async_write_ha_state()

    @property
    def hvac_modes(self) -> list[str]:
        """Return the list of available HVAC modes."""
        return [STATE_ON, STATE_OFF]

    @property
    def min_temp(self) -> float:
        """Return the minimum allowed temperature."""
        return 30.0

    @property
    def max_temp(self) -> float:
        """Return the maximum allowed temperature."""
        return 80.0

    @property
    def device_info(self) -> dict:
        """Return device information so that both entities share the same device."""
        return {
            "identifiers": {(DOMAIN, self._entry.data.get("mac"))},
            "name": self._entry.data.get("name", "Gree Versati"),
            "manufacturer": "Gree",
            "model": "Versati Air to Water Heat Pump",
        }
