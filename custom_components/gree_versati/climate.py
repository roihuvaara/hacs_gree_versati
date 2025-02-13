"""Climate platform for Gree Versati."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import GreeVersatiDataUpdateCoordinator
from .entity import GreeVersatiEntity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GreeVersatiClimate(data.coordinator, data.client)])

class GreeVersatiClimate(GreeVersatiEntity, ClimateEntity):
    """Representation of a Gree Versati Climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
        client,
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{client.mac}_climate"
        self._attr_name = "Gree Versati Climate"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temp = self.coordinator.data.get("water_out_temp")
        LOGGER.debug(f"Current temperature: {temp}")
        return temp

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if self.hvac_mode == HVACMode.HEAT:
            temp = self.coordinator.data.get("heat_temp_set")
            LOGGER.debug(f"Target heat temperature: {temp}")
            return temp
        elif self.hvac_mode == HVACMode.COOL:
            temp = self.coordinator.data.get("cool_temp_set")
            LOGGER.debug(f"Target cool temperature: {temp}")
            return temp
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation mode."""
        if not self.coordinator.data.get("power"):
            return HVACMode.OFF
        mode = self.coordinator.data.get("mode")
        if mode == 4:
            return HVACMode.HEAT
        elif mode == 1:
            return HVACMode.COOL
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self._client.set_temperature(temperature, self.hvac_mode)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        await self._client.set_hvac_mode(hvac_mode)
        await self.coordinator.async_request_refresh()
