"""Floor Heating climate entity for the Gree Versati integration."""
from __future__ import annotations
import logging

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.const import TEMP_CELSIUS
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GreeVersatiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the Gree Versati floor heating climate entity."""
    coordinator: GreeVersatiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([GreeVersatiFloorHeatingClimate(coordinator, entry)], True)


class GreeVersatiFloorHeatingClimate(CoordinatorEntity, ClimateEntity):
    """Representation of the Gree Versati Floor Heating Climate entity."""

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the floor heating climate entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = entry.data.get("name", "Gree Versati Floor Heating")
        self._attr_unique_id = f"{entry.data.get('mac')}_floorheating"
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._target_temperature: float | None = None

    @property
    def current_temperature(self) -> float | None:
        """Return the current floor heating temperature.

        This example assumes the coordinator's data is a dict with a key 'floor_temp'.
        Adjust as needed.
        """
        if isinstance(self.coordinator.data, dict):
            return self.coordinator.data.get("floor_temp")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target floor heating temperature."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set a new target temperature for floor heating."""
        new_temp = kwargs.get("temperature")
        if new_temp is None:
            return
        # Here you would call your device API to update the floor heating target temperature.
        self._target_temperature = new_temp
        _LOGGER.debug("Setting floor heating target temperature to %s", new_temp)
        self.async_write_ha_state()

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode for floor heating."""
        return HVACMode.HEAT if self._target_temperature is not None else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set a new HVAC mode for floor heating."""
        if hvac_mode == HVACMode.OFF:
            self._target_temperature = None
            _LOGGER.debug("Floor heating turned off.")
        else:
            if self._target_temperature is None:
                self._target_temperature = 22.0  # default target temperature for floor heating
            _LOGGER.debug("Floor heating turned on. Target temperature: %s", self._target_temperature)
        self.async_write_ha_state()

    @property
    def hvac_modes(self) -> list[str]:
        """Return the list of available HVAC modes for floor heating."""
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def min_temp(self) -> float:
        """Return the minimum allowed temperature for floor heating."""
        return 16.0

    @property
    def max_temp(self) -> float:
        """Return the maximum allowed temperature for floor heating."""
        return 30.0

    @property
    def device_info(self) -> dict:
        """Return device information so that both entities share the same device."""
        return {
            "identifiers": {(DOMAIN, self._entry.data.get("mac"))},
            "name": self._entry.data.get("name", "Gree Versati"),
            "manufacturer": "Gree",
            "model": "Versati Air to Water Heat Pump",
        }
