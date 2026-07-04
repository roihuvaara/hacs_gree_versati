"""
Custom integration to integrate Gree Versati Air to Water heat pump with Home Assistant.

For more details about this integration, please refer to
https://github.com/roihuvaara/hacs_gree_versati
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .client import GreeVersatiClient
from .const import CONF_IP, DOMAIN, LOGGER
from .coordinator import GreeVersatiDataUpdateCoordinator
from .data import GreeVersatiData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import GreeVersatiConfigEntry

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.WATER_HEATER,
]


async def async_setup_entry(hass: HomeAssistant, entry: GreeVersatiConfigEntry) -> bool:
    """
    Set up the Gree Versati integration from a config entry.

    The config entry is expected to contain:
      - CONF_IP: the device's IP address
      - CONF_PORT: the device's port (usually 7000)
      - CONF_MAC: the device's MAC address
      - CONF_NAME: the device name (or a fallback value)
      - "key": the negotiated binding key
      - "cipher_type": the negotiated cipher scheme (absent on old entries)
    """
    LOGGER.debug("Starting setup of Gree Versati integration")

    ip = entry.data[CONF_IP]
    port = entry.data[CONF_PORT]
    mac = entry.data[CONF_MAC]
    name = entry.data[CONF_NAME]
    key = entry.data.get("key")
    cipher_type = entry.data.get("cipher_type")

    # Create the client using the stored connection parameters and key.
    client = GreeVersatiClient(
        ip=ip, port=port, mac=mac, key=key, cipher_type=cipher_type
    )

    try:
        LOGGER.debug("Initializing device connection")
        await client.initialize()
        LOGGER.debug("Device initialization successful")
    except (ConnectionError, OSError) as exc:
        error_msg = f"Failed to initialize device '{name}' ({mac}): {exc}"
        raise ConfigEntryNotReady(error_msg) from exc

    # Persist negotiated credentials (old entries lack cipher_type, and
    # entries created before the bind fix stored key=None)
    if key != client.key or cipher_type != client.cipher_type:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "key": client.key, "cipher_type": client.cipher_type},
        )

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
        config_entry=entry,
    )
    LOGGER.debug(
        "Coordinator created with update interval: %s", coordinator.update_interval
    )

    # Link everything together
    data.coordinator = coordinator
    entry.runtime_data = data
    LOGGER.debug("Coordinator linked to config entry and runtime data")

    LOGGER.debug("Performing initial data refresh")
    # Raises ConfigEntryNotReady on failure, so HA retries automatically
    await coordinator.async_config_entry_first_refresh()
    LOGGER.debug("Initial data refresh successful")

    # Forward the config entry setup to platforms
    LOGGER.debug("Setting up platforms")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    LOGGER.debug("Gree Versati integration setup complete")
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GreeVersatiConfigEntry
) -> bool:
    """Unload a config entry (runtime_data is discarded by HA)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
