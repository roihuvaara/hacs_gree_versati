"""DataUpdateCoordinator for gree_versati."""

from __future__ import annotations

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            if (
                not hasattr(self.config_entry, "runtime_data")
                or not self.config_entry.runtime_data
            ):
                raise NoRuntimeDataError  # noqa: TRY301

            data = await self.config_entry.runtime_data.client.async_get_data()
            LOGGER.debug("Updated data: %s", data)
            return data
        except Exception as exc:
            LOGGER.error("Error fetching data from device: %s", exc)
            error_msg = f"Communication error: {exc}"
            raise UpdateFailed(error_msg) from exc
