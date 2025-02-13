"""BlueprintEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import GreeVersatiDataUpdateCoordinator


class GreeVersatiEntity(CoordinatorEntity[GreeVersatiDataUpdateCoordinator]):
    """Base class for Gree Versati entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )

    @property
    def device_info(self):
        """Return device information."""
        model_series = self.coordinator.data.get("versati_series")
        model_name = model_series if model_series else "Versati"
        
        return {
            "identifiers": {("gree_versati", self.coordinator.config_entry.entry_id)},
            "name": self.coordinator.config_entry.title,
            "manufacturer": "Gree",
            "model": model_name,
        }
