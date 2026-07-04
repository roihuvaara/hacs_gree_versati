"""Climate platform for Gree Versati."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import (
    COOL_TEMP_MAX,
    COOL_TEMP_MIN,
    COOLING_MODES,
    DHW_MODES,
    HEAT_TEMP_MAX,
    HEAT_TEMP_MIN,
    HEATING_MODES,
    LOGGER,
)
from .entity import GreeVersatiEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GreeVersatiDataUpdateCoordinator
    from .data import GreeVersatiConfigEntry

# All I/O goes through the coordinator/client; no parallel entity updates
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati climate platform."""
    async_add_entities([GreeVersatiClimate(entry.runtime_data.coordinator)])


class GreeVersatiClimate(GreeVersatiEntity, ClimateEntity):
    """Representation of a Gree Versati Climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_has_entity_name = True
    _attr_translation_key = "space_heating"
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        # client is now available as self._client from GreeVersatiEntity
        # Override the unique_id from GreeVersatiEntity with entity-specific ID
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_space_heating"
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
        ]

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
        if mode in HEATING_MODES:
            return HVACMode.HEAT
        if mode in COOLING_MODES:
            return HVACMode.COOL
        # hot-water-only (Mod=2): no space heating/cooling running
        return HVACMode.OFF

    @property
    def min_temp(self) -> float:
        """Return the minimum settable water-out temperature."""
        if self.hvac_mode == HVACMode.COOL:
            return COOL_TEMP_MIN
        return HEAT_TEMP_MIN

    @property
    def max_temp(self) -> float:
        """Return the maximum settable water-out temperature."""
        if self.hvac_mode == HVACMode.COOL:
            return COOL_TEMP_MAX
        return HEAT_TEMP_MAX

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
        # Combine requested HVAC mode with current DHW participation
        # (DHW is part of the device Mod value, not a separate flag)
        dhw_active = (
            bool(self.coordinator.data.get("power"))
            and self.coordinator.data.get("mode") in DHW_MODES
        )
        if hvac_mode == HVACMode.OFF:
            combined = "hot_water" if dhw_active else "off"
        elif hvac_mode == HVACMode.HEAT:
            combined = "heat_hot_water" if dhw_active else "heat"
        elif hvac_mode == HVACMode.COOL:
            combined = "cool_hot_water" if dhw_active else "cool"
        else:
            combined = "off"

        await self._client.set_device_mode(combined)
        await self.coordinator.async_request_refresh()
