"""BlueprintEntity class."""

from __future__ import annotations

from functools import cached_property

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import GreeVersatiDataUpdateCoordinator


class NoRuntimeDataError(HomeAssistantError):
    """Error when runtime data is not available."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("No runtime data available")


class NoEntryIdError(HomeAssistantError):
    """Error when entry ID is not available."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("No entry ID available")


class GreeVersatiEntity(CoordinatorEntity[GreeVersatiDataUpdateCoordinator]):
    """Base class for Gree Versati entities."""

    _attr_attribution: str | None = ATTRIBUTION
    _attr_has_entity_name: bool = True

    def __init__(self, coordinator: GreeVersatiDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)

        if (
            not hasattr(coordinator.config_entry, "runtime_data")
            or not coordinator.config_entry.runtime_data
        ):
            raise NoRuntimeDataError

        self._client = coordinator.config_entry.runtime_data.client
        if not coordinator.config_entry.entry_id:
            raise NoEntryIdError

        self._attr_unique_id = coordinator.config_entry.entry_id

    @cached_property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        if not self.coordinator.data:
            return DeviceInfo(
                identifiers={(DOMAIN, self._client.mac)},
                name=self.coordinator.config_entry.title or "Unknown",
                manufacturer="Gree",
                model="Versati",
            )

        model_series = self.coordinator.data.get("versati_series")
        model_name = f"Versati ({model_series})" if model_series else "Versati"

        return DeviceInfo(
            identifiers={(DOMAIN, self._client.mac)},
            name=self.coordinator.config_entry.title or "Unknown",
            manufacturer="Gree",
            model=model_name,
        )
