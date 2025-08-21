"""Binary sensor platform for gree_versati."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import ATTRIBUTION, DOMAIN
from .naming import get_entry_name

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import GreeVersatiDataUpdateCoordinator
    from .data import GreeVersatiConfigEntry

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="gree_versati",
        name="Gree Versati Binary Sensor",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator
    if coordinator is None:
        return

    async_add_entities(
        GreeVersatiBinarySensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class GreeVersatiBinarySensor(BinarySensorEntity):
    """gree_versati binary_sensor class."""

    _attr_attribution: str | None = ATTRIBUTION
    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: GreeVersatiDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        self.coordinator = coordinator
        self.entity_description = entity_description
        self._attr_unique_id = coordinator.config_entry.entry_id

    @cached_property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        if not self.coordinator.data:
            return DeviceInfo(
                identifiers={
                    (DOMAIN, self.coordinator.config_entry.runtime_data.client.mac)
                },
                name=get_entry_name(self.coordinator.config_entry),
                manufacturer="Gree",
                model="Versati",
            )

        model_series = self.coordinator.data.get("versati_series")
        model_name = f"Versati ({model_series})" if model_series else "Versati"

        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.config_entry.runtime_data.client.mac)
            },
            name=get_entry_name(self.coordinator.config_entry),
            manufacturer="Gree",
            model=model_name,
        )

    @cached_property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("title", "") == "foo"
