"""Water heater platform for Gree Versati."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GreeVersatiDataUpdateCoordinator
    from .data import GreeVersatiConfigEntry

from .const import (
    CONF_DHW_TEMP_MAX,
    CONF_DHW_TEMP_MIN,
    COOLING_MODES,
    DHW_MODES,
    DHW_TEMP_MAX,
    DHW_TEMP_MIN,
    HEATING_MODES,
    LOGGER,
    OPERATION_LIST,
    OPERATION_MODE_HEAT_PUMP,
    OPERATION_MODE_OFF,
    OPERATION_MODE_PERFORMANCE,
)
from .entity import GreeVersatiEntity

# All I/O goes through the coordinator/client; no parallel entity updates
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati water heater platform."""
    async_add_entities([GreeVersatiWaterHeater(entry.runtime_data.coordinator)])


class GreeVersatiWaterHeater(GreeVersatiEntity, WaterHeaterEntity):
    """Representation of a Gree Versati Water Heater device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = OPERATION_LIST
    _attr_has_entity_name = True
    _attr_translation_key = "water_heater"
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
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
        power = bool(self.coordinator.data.get("power"))
        mode = self.coordinator.data.get("mode")
        if not power or mode not in DHW_MODES:
            operation = OPERATION_MODE_OFF
        elif self.coordinator.data.get("fast_heat_water"):
            operation = OPERATION_MODE_PERFORMANCE
        else:
            operation = OPERATION_MODE_HEAT_PUMP
        LOGGER.debug("DHW operation mode: %s", operation)
        return operation

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        # Unlike climate, the water_heater component does not validate the
        # target against min/max, so enforce the configured limits here
        if not self.min_temp <= temperature <= self.max_temp:
            msg = (
                f"Target temperature {temperature}°C is outside the allowed "
                f"range {self.min_temp:.0f}-{self.max_temp:.0f}°C"
            )
            raise ServiceValidationError(msg)
        await self._client.set_dhw_temperature(temperature)
        self.coordinator.async_apply_optimistic(hot_water_temp_set=int(temperature))

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        # DHW participation is part of the device Mod value: combine the
        # requested DHW state with the current space heating/cooling mode.
        power = bool(self.coordinator.data.get("power"))
        mode_val = self.coordinator.data.get("mode")

        if power and mode_val in HEATING_MODES:
            base = "heat"
        elif power and mode_val in COOLING_MODES:
            base = "cool"
        else:
            base = None

        if operation_mode == OPERATION_MODE_OFF:
            combined = base or "off"
        elif base:
            combined = f"{base}_hot_water"
        else:
            combined = "hot_water"

        await self._client.set_device_mode(combined)

        # FastHtWter is only the boost flag, never the DHW on/off switch
        extra = {}
        if operation_mode != OPERATION_MODE_OFF:
            dhw_boost = (
                "performance"
                if operation_mode == OPERATION_MODE_PERFORMANCE
                else "normal"
            )
            await self._client.set_dhw_mode(dhw_boost)
            extra["fast_heat_water"] = dhw_boost == "performance"

        # Publish the expected state; the unit reports transitional values
        # right after a mode change, so an immediate poll would lie
        self.coordinator.async_apply_optimistic_device_mode(combined, **extra)

    async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn DHW on in normal (heat pump) operation."""
        await self.async_set_operation_mode(OPERATION_MODE_HEAT_PUMP)

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn DHW off."""
        await self.async_set_operation_mode(OPERATION_MODE_OFF)

    @property
    def min_temp(self) -> float:
        """Return the minimum allowed temperature."""
        value = self.coordinator.config_entry.options.get(
            CONF_DHW_TEMP_MIN, DHW_TEMP_MIN
        )
        return min(max(value, DHW_TEMP_MIN), DHW_TEMP_MAX)

    @property
    def max_temp(self) -> float:
        """Return the maximum allowed temperature."""
        value = self.coordinator.config_entry.options.get(
            CONF_DHW_TEMP_MAX, DHW_TEMP_MAX
        )
        return min(max(value, DHW_TEMP_MIN), DHW_TEMP_MAX)
