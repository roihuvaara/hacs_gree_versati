"""DataUpdateCoordinator for gree_versati."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from .data import GreeVersatiConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class GreeVersatiDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the device."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            name=name,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            data = await self.config_entry.runtime_data.client.async_get_data()
            LOGGER.debug(f"Updated data: {data}")
            return data
        except Exception as exc:
            LOGGER.error("Error fetching data from device: %s", exc)
            raise UpdateFailed(f"Error communicating with device: {exc}") from exc
