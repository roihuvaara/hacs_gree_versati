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
    _attr_target_temperature_step = 1
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
        self._attr_unique_id = f"gree_versati_{client.mac}"

    @property
    def translation_key(self):
        """Return the translation key to translate the entity's name."""
        return "climate"

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

        # Use the client's set_temperature method with the current HVAC mode
        mode = None
        if self.hvac_mode == HVACMode.HEAT:
            mode = "heat"
        elif self.hvac_mode == HVACMode.COOL:
            mode = "cool"
            
        await self._client.set_temperature(temperature, mode=mode)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        await self._client.set_hvac_mode(hvac_mode)
        await self.coordinator.async_request_refresh()
