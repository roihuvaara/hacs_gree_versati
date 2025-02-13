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
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant


from .client import GreeVersatiClient
from .const import DOMAIN, LOGGER, CONF_IP
from .coordinator import GreeVersatiDataUpdateCoordinator
from .data import GreeVersatiData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

    from .data import GreeVersatiConfigEntry

PLATFORMS: list[Platform] = [
    # Platform.SENSOR,
    # Platform.DEVICE,
    # Platform.BINARY_SENSOR,
    # Platform.SWITCH,
    Platform.CLIMATE,
    Platform.WATER_HEATER,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Set up the integration from YAML if present.
    
    Since we are using a config flow (UI based configuration), this function only ensures
    that the integration's data container exists.
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up the Gree Versati integration from a config entry.
    
    The config entry is expected to contain:
      - CONF_IP: the device's IP address
      - CONF_PORT: the device's port (usually 7000)
      - CONF_MAC: the device's MAC address
      - CONF_NAME: the device name (or a fallback value)
      - "key": the negotiated binding key
    """
    ip = entry.data[CONF_IP]
    port = entry.data[CONF_PORT]
    mac = entry.data[CONF_MAC]
    name = entry.data[CONF_NAME]
    key = entry.data["key"]

    # Create the client using the stored connection parameters and key.
    client = GreeVersatiClient(ip=ip, port=port, mac=mac, key=key)

    try:
        # Initialize the client (this will create the device instance and bind it using the stored key).
        await client.initialize()
    except Exception as exc:
        LOGGER.error("Failed to initialize device '%s' (%s): %s", name, mac, exc)
        return False

    # Create the data container first
    data = GreeVersatiData(
        client=client,
        coordinator=None,  # We'll set this after creating the coordinator
    )

    # Set up the data update coordinator that will periodically fetch data from the device.
    coordinator = GreeVersatiDataUpdateCoordinator(
        hass=hass,
        name=DOMAIN,
        logger=LOGGER,
        update_interval=timedelta(seconds=5),
    )

    # Now link everything together
    data.coordinator = coordinator
    coordinator.config_entry = entry
    coordinator.config_entry.runtime_data = data

    try:
        # Perform an initial data refresh
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        LOGGER.error("Failed initial data refresh for '%s': %s", name, exc)
        return False

    # Store everything in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = data

    # Forward the config entry setup to the supported platforms (e.g. sensor and device).
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.

    This function unloads the platforms and removes the integration's stored data.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
