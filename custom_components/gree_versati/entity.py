"""Base entity for Gree Versati."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GreeVersatiDataUpdateCoordinator
from .naming import get_entry_name


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

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        device_name = get_entry_name(self.coordinator.config_entry)

        data = self.coordinator.data or {}
        model_series = data.get("versati_series")
        model_name = f"Versati ({model_series})" if model_series else "Versati"

        connections: set[tuple[str, str]] = set()
        if isinstance(self._client.mac, str) and self._client.mac:
            connections.add((CONNECTION_NETWORK_MAC, format_mac(self._client.mac)))

        return DeviceInfo(
            identifiers={(DOMAIN, self._client.mac)},
            connections=connections,
            name=device_name,
            manufacturer="Gree",
            model=model_name,
        )
