"""
Custom integration to integrate Gree Versati Air to Water heat pump with Home Assistant.

For more details about this integration, please refer to
https://github.com/roihuvaara/hacs_gree_versati
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

# from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .client import GreeVersatiClient
from .const import CONF_IP, DOMAIN, LOGGER
from .coordinator import GreeVersatiDataUpdateCoordinator
from .data import GreeVersatiData
from .package_helper import force_update_dependency

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [
    # Platform.SENSOR,
    # Platform.DEVICE,
    # Platform.BINARY_SENSOR,
    # Platform.SWITCH,
    Platform.CLIMATE,
    Platform.WATER_HEATER,
    Platform.SELECT,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Set up the integration from YAML if present.

    Since we are using a config flow (UI based configuration), this function only
    ensures that the integration's data container exists.
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
    LOGGER.debug("Starting setup of Gree Versati integration")

    # Force update/reinstall dependency from manifest.json
    await force_update_dependency(hass)

    ip = entry.data[CONF_IP]
    port = entry.data[CONF_PORT]
    mac = entry.data[CONF_MAC]
    name = entry.data[CONF_NAME]
    key = entry.data["key"]

    # Ensure the entry has a unique ID based on the MAC address
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=mac)

    # Create the client using the stored connection parameters and key.
    client = GreeVersatiClient(ip=ip, port=port, mac=mac, key=key, name=name)

    try:
        LOGGER.debug("Initializing device connection")
        await client.initialize()
        LOGGER.debug("Device initialization successful")
    except Exception as exc:  # noqa: BLE001
        # We catch all exceptions here to ensure setup can fail gracefully
        LOGGER.error("Failed to initialize device '%s' (%s): %s", name, mac, exc)
        return False

    # Create the data container first
    data = GreeVersatiData(
        client=client,
        coordinator=None,  # We'll set this after creating the coordinator
    )

    # Set up the data update coordinator
    LOGGER.debug("Creating data update coordinator")
    coordinator = GreeVersatiDataUpdateCoordinator(
        hass=hass,
        name=DOMAIN,
        logger=LOGGER,
        update_interval=timedelta(seconds=30),
    )
    LOGGER.debug(
        "Coordinator created with update interval: %s", coordinator.update_interval
    )

    # Link everything together
    data.coordinator = coordinator
    coordinator.config_entry = entry
    coordinator.config_entry.runtime_data = data
    LOGGER.debug("Coordinator linked to config entry and runtime data")

    # Register the device in the device registry
    from homeassistant.helpers import device_registry as dr

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mac)},
        name=name or "Gree Versati",
        manufacturer="Gree",
        model="Versati",
    )
    LOGGER.debug("Device registered in device registry")

    try:
        LOGGER.debug("Performing initial data refresh")
        await coordinator.async_config_entry_first_refresh()
        LOGGER.debug("Initial data refresh successful")
    except Exception as exc:  # noqa: BLE001
        # We catch all exceptions here to ensure setup can fail gracefully
        LOGGER.error("Failed initial data refresh for '%s': %s", name, exc)
        return False

    # Store everything in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = data

    # Forward the config entry setup to platforms
    LOGGER.debug("Setting up platforms")
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    LOGGER.debug("Gree Versati integration setup complete")
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
