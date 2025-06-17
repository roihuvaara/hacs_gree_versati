"""Water heater platform for Gree Versati."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GreeVersatiDataUpdateCoordinator

from .const import DOMAIN, LOGGER, OPERATION_LIST
from .entity import GreeVersatiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati water heater platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GreeVersatiWaterHeater(data.coordinator)])


class GreeVersatiWaterHeater(GreeVersatiEntity, WaterHeaterEntity):
    """Representation of a Gree Versati Water Heater device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = OPERATION_LIST
    _attr_has_entity_name = True
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
    ) -> None:
        """Initialize the water heater device."""
        super().__init__(coordinator)
        # client is now available as self._client from GreeVersatiEntity
        # Override the unique_id from GreeVersatiEntity with entity-specific ID
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_water_heater"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def translation_key(self) -> str | None:
        """Return the translation key to translate the entity's name."""
        return "water_heater"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temp = self.coordinator.data.get("hot_water_temp")
        LOGGER.debug("DHW current temperature: %s", temp)
        return temp

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        temp = self.coordinator.data.get("hot_water_temp_set")
        LOGGER.debug("DHW target temperature: %s", temp)
        return temp

    @property
    def current_operation(self) -> str | None:
        """Return current operation."""
        mode = (
            "performance" if self.coordinator.data.get("fast_heat_water") else "normal"
        )
        LOGGER.debug("DHW operation mode: %s", mode)
        return mode

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
    def hvac_mode(self) -> str | None:
        """
        Return the current HVAC mode.

        In this example, if a target temperature is set, the water heater is 'on',
        otherwise it's 'off'.
        """
        return "on" if self.target_temperature is not None else "off"

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set the HVAC mode for the water heater."""
        target_temp = None
        if hvac_mode == "off":
            # Set to None to turn off
            pass  # We'll just pass None to async_set_temperature
        elif self.target_temperature is None:
            # Set default target temperature if currently None
            target_temp = 50.0
        else:
            target_temp = self.target_temperature

        await self.async_set_temperature(temperature=target_temp)

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
