"""Climate platform for Gree Versati."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_EXTERNAL_TEMP_SENSOR,
    CONF_USE_WATER_TEMP_AS_CURRENT,
    COOL_MODE,
    DOMAIN,
    HEAT_MODE,
    LOGGER,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .client import GreeVersatiClient
    from .coordinator import GreeVersatiDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GreeVersatiClimate(hass, entry, data.coordinator, data.client)])


class GreeVersatiClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Gree Versati Climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_has_entity_name = True
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
    ]  # Basic modes for HA

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: GreeVersatiDataUpdateCoordinator,
        client: GreeVersatiClient,
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self.hass = hass
        self.entry = entry
        self._client = client
        # Use MAC address for unique_id to ensure consistency
        self._attr_unique_id = f"{client.mac}_climate"
        self._attr_name = "Space Heating"
        # Set a consistent device identifier
        self._device_id = client.mac or "unknown"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def translation_key(self) -> str:
        """Return the translation key to translate the entity's name."""
        return "climate"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Use the entry title or a meaningful default
        device_name = self.entry.title or "Gree Versati"

        # Use MAC address as the consistent device identifier
        mac_address = self._client.mac or "unknown"

        device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=device_name,
            manufacturer="Gree",
            model="Versati",
            sw_version=self.coordinator.data.get("versati_series", "Unknown")
            if self.coordinator.data
            else "Unknown",
        )

        return device_info

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        # First check if we have an external temperature sensor configured
        external_sensor = self.entry.options.get(CONF_EXTERNAL_TEMP_SENSOR)

        if external_sensor:
            # Try to get the state from the external sensor
            try:
                sensor_state = self.hass.states.get(external_sensor)
                if sensor_state and sensor_state.state not in (
                    None,
                    "unknown",
                    "unavailable",
                ):
                    temp = float(sensor_state.state)
                    LOGGER.debug(
                        "Using external sensor for current temperature: %s = %s",
                        external_sensor,
                        temp,
                    )
                    return temp
            except (ValueError, TypeError) as ex:
                LOGGER.warning(
                    "Could not use external temperature sensor %s: %s",
                    external_sensor,
                    ex,
                )

        # If no external sensor or an error occurred, use water temp if configured to do so
        if self.entry.options.get(CONF_USE_WATER_TEMP_AS_CURRENT, False):
            temp = self.coordinator.data.get("water_out_temp")
            LOGGER.debug("Using water temperature as current temperature: %s", temp)
            return temp

        # Return None if we don't have a valid temperature source
        LOGGER.debug("No temperature source available, returning None")
        return None

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation mode."""
        if not self.coordinator.data:
            return HVACMode.OFF

        if not self.coordinator.data.get("power", False):
            return HVACMode.OFF

        mode = self.coordinator.data.get("mode")
        if mode == HEAT_MODE:
            return HVACMode.HEAT
        if mode == COOL_MODE:
            return HVACMode.COOL

        return HVACMode.OFF

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

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        # Mode control is handled by the select entity, so this is a no-op
        pass
