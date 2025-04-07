"""Climate platform for Gree Versati."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COOL_MODE, DOMAIN, HEAT_MODE, LOGGER

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .client import GreeVersatiClient
    from .coordinator import GreeVersatiDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GreeVersatiClimate(data.coordinator, data.client)])


class GreeVersatiClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Gree Versati Climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_has_entity_name = True
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
        client: GreeVersatiClient,
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = "space_heating"
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
        ]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def translation_key(self) -> str:
        """Return the translation key to translate the entity's name."""
        return "climate"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temp = self.coordinator.data.get("water_out_temp")
        LOGGER.debug("Current temperature: %s", temp)
        return temp

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if self.hvac_mode == HVACMode.HEAT:
            temp = self.coordinator.data.get("heat_temp_set")
            LOGGER.debug("Target heat temperature: %s", temp)
            return temp
        if self.hvac_mode == HVACMode.COOL:
            temp = self.coordinator.data.get("cool_temp_set")
            LOGGER.debug("Target cool temperature: %s", temp)
            return temp
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation mode."""
        if not self.coordinator.data.get("power"):
            return HVACMode.OFF
        mode = self.coordinator.data.get("mode")
        if mode == HEAT_MODE:
            return HVACMode.HEAT
        if mode == COOL_MODE:
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
