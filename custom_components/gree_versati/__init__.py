"""
Custom integration to integrate Gree Versati Air to Water heat pump with Home Assistant.

For more details about this integration, please refer to
https://github.com/roihuvaara/hacs_gree_versati
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

# from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.const import Platform
from homeassistant.exceptions import PlatformNotReady

# from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .client import GreeVersatiClient
from .const import DOMAIN, LOGGER
from .coordinator import GreeVersatiDataUpdateCoordinator
from .data import GreeVersatiData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

    from .data import GreeVersatiConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.DEVICE,
    # Platform.BINARY_SENSOR,
    # Platform.SWITCH,
]


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the platform."""
    client = GreeVersatiClient()
    try:
        await client.run_discovery()
    except ConnectionError:
        raise PlatformNotReady("err") from None


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = GreeVersatiDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=5),
    )
    entry.runtime_data = GreeVersatiData(
        client=GreeVersatiClient(),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    try:
        # Find devices and bind
        await entry.runtime_data.client.run_discovery()
        return True
    except:
        return False
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    # await coordinator.async_config_entry_first_refresh()

    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # entry.async_on_unload(entry.add_update_listener(async_reload_entry))


async def async_unload_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: GreeVersatiConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
