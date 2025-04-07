"""DataUpdateCoordinator for gree_versati."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


class NoRuntimeDataError(UpdateFailed):
    """Error when runtime data is not available."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("No runtime data available")


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class GreeVersatiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the device."""

    config_entry: ConfigEntry
    _first_update_done: bool = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        LOGGER.debug("Coordinator update called - polling cycle starting")
        try:
            if (
                not hasattr(self.config_entry, "runtime_data")
                or not self.config_entry.runtime_data
            ):
                LOGGER.error("No runtime data available for coordinator update")
                raise NoRuntimeDataError  # noqa: TRY301

            LOGGER.debug("Fetching updated data from device")
            data = await self.config_entry.runtime_data.client.async_get_data()

            # Add a small delay after the first data update
            if not self._first_update_done:
                LOGGER.debug("First update - adding delay to allow device to respond")
                await asyncio.sleep(2.0)
                # Check if data values are None, if so, fetch again
                if all(value is None for value in data.values()):
                    LOGGER.debug(
                        "Initial data contains all None values, fetching again"
                    )
                    data = await self.config_entry.runtime_data.client.async_get_data()
                self._first_update_done = True

            LOGGER.debug("Updated data received: %s", data)
            return data
        except Exception as exc:
            LOGGER.error("Error fetching data from device: %s", exc)
            error_msg = f"Communication error: {exc}"
            raise UpdateFailed(error_msg) from exc
