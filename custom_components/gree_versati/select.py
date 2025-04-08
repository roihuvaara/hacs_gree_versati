"""Select platform for the Gree Versati integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    COOL_DHW_MODE,
    COOL_MODE,
    HEAT_DHW_MODE,
    HEAT_MODE,
    DOMAIN,
)
from .coordinator import GreeVersatiDataUpdateCoordinator
from .entity import GreeVersatiEntity

# Define available operating modes
OPERATING_MODES = [
    HEAT_MODE,
    COOL_MODE,
    HEAT_DHW_MODE,
    COOL_DHW_MODE,
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Versati select platform."""
    coordinator: GreeVersatiDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities([GreeVersatiOperatingModeSelect(coordinator, config_entry)])


class GreeVersatiOperatingModeSelect(GreeVersatiEntity, SelectEntity):
    """Representation of a Gree Versati operating mode select."""

    _attr_name = "Operating Mode"
    _attr_unique_id = "operating_mode"
    _attr_options = OPERATING_MODES
    _attr_icon = "mdi:heat-pump"

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_device_info = self._get_device_info()

    def _get_device_info(self) -> DeviceInfo:
        """Return device information."""
        device_name = self._config_entry.title or "Gree Versati"
        mac_address = self._config_entry.data.get("mac_address", "unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=device_name,
            manufacturer="Gree",
            model="Versati",
        )

    @property
    def current_option(self) -> str | None:
        """Return the current operating mode."""
        return self.coordinator.data.get("operating_mode")

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        client = self.coordinator.config_entry.runtime_data.client
        await client.set_hvac_mode(option)
        await self.coordinator.async_refresh()
