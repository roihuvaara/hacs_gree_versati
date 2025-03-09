"""BlueprintEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import GreeVersatiDataUpdateCoordinator


class GreeVersatiEntity(CoordinatorEntity[GreeVersatiDataUpdateCoordinator]):
    """Base class for Gree Versati entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._client = coordinator.config_entry.runtime_data.client
        self._attr_unique_id = coordinator.config_entry.entry_id

    @property
    def device_info(self):
        """Return device information."""
        model_series = self.coordinator.data.get("versati_series")
        model_name = f"Versati ({model_series})" if model_series else "Versati"
        
        return {
            "identifiers": {(DOMAIN, self._client.mac)},
            "name": self.coordinator.config_entry.title,
            "manufacturer": "Gree",
            "model": model_name,
        }
