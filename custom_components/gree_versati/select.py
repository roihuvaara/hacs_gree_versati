"""Select platform for device mode control."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity

from .const import DOMAIN
from .entity import GreeVersatiEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GreeVersatiDataUpdateCoordinator


MODE_OPTIONS: list[str] = [
    "off",
    "cool",
    "heat",
    "hot_water",
    "cool_hot_water",
    "heat_hot_water",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device mode select platform."""
    # Support both patterns used in tests/component: entry.runtime_data or hass.data
    coordinator: GreeVersatiDataUpdateCoordinator | None = None
    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data and getattr(runtime_data, "coordinator", None):
        coordinator = runtime_data.coordinator
    else:
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if data:
            coordinator = data.get("coordinator")

    if not coordinator:
        return

    async_add_entities([GreeVersatiDeviceModeSelect(coordinator)])


class GreeVersatiDeviceModeSelect(GreeVersatiEntity, SelectEntity):
    """Select entity to control combined device mode."""

    _attr_has_entity_name = True
    _attr_options = MODE_OPTIONS

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_device_mode"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option (device mode)."""
        await self._client.set_device_mode(option)
        await self.coordinator.async_request_refresh()
