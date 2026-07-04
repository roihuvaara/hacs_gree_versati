"""Select platform for device mode control."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity

from .const import MOD_TO_DEVICE_MODE
from .entity import GreeVersatiEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GreeVersatiDataUpdateCoordinator
    from .data import GreeVersatiConfigEntry


MODE_OPTIONS: list[str] = [
    "off",
    "cool",
    "heat",
    "hot_water",
    "cool_hot_water",
    "heat_hot_water",
]

# All I/O goes through the coordinator/client; no parallel entity updates
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device mode select platform."""
    async_add_entities([GreeVersatiDeviceModeSelect(entry.runtime_data.coordinator)])


class GreeVersatiDeviceModeSelect(GreeVersatiEntity, SelectEntity):
    """Select entity to control combined device mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "device_mode"
    _attr_options = MODE_OPTIONS

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_device_mode"

    @property
    def current_option(self) -> str | None:
        """Return the current combined device mode."""
        data = self.coordinator.data or {}
        if not data.get("power"):
            return "off"
        return MOD_TO_DEVICE_MODE.get(data.get("mode"))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option (device mode)."""
        await self._client.set_device_mode(option)
        await self.coordinator.async_request_refresh()
