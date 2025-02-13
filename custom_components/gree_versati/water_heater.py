"""Water heater platform for Gree Versati."""
from __future__ import annotations

from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GreeVersatiDataUpdateCoordinator
from .entity import GreeVersatiEntity

OPERATION_LIST = ["normal", "performance"]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati water heater platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GreeVersatiWaterHeater(data.coordinator, data.client)])

class GreeVersatiWaterHeater(GreeVersatiEntity, WaterHeaterEntity):
    """Representation of a Gree Versati Water Heater device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = OPERATION_LIST
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
        client,
    ) -> None:
        """Initialize the water heater device."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{client.mac}_water_heater"
        self._attr_name = "Gree Versati Water Heater"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get("hot_water_temp")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data.get("hot_water_temp_set")

    @property
    def current_operation(self) -> str | None:
        """Return current operation."""
        return "performance" if self.coordinator.data.get("fast_heat_water") else "normal"

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self._client.set_dhw_temperature(temperature)
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        await self._client.set_dhw_mode(operation_mode)
        await self.coordinator.async_request_refresh()

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode.

        In this example, if a target temperature is set, the water heater is 'on',
        otherwise it's 'off'.
        """
        return "on" if self.target_temperature is not None else "off"

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set the HVAC mode for the water heater."""
        if hvac_mode == "off":
            self.target_temperature = None
        else:
            if self.target_temperature is None:
                self.target_temperature = 50.0  # default target temperature
        await self.async_set_temperature(temperature=self.target_temperature)

    @property
    def hvac_modes(self) -> list[str]:
        """Return the list of available HVAC modes."""
        return ["on", "off"]

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
            "identifiers": {(DOMAIN, self._client.mac)},
            "name": self._attr_name,
            "manufacturer": "Gree",
            "model": "Versati Air to Water Heat Pump",
        }
