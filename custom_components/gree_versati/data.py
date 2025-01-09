"""Custom types for gree_versati."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .client import GreeVersatiClient
    from .coordinator import GreeVersatiDataUpdateCoordinator


type GreeVersatiConfigEntry = ConfigEntry[GreeVersatiData]


@dataclass
class GreeVersatiData:
    """Data for the Gree Versati integration."""

    client: GreeVersatiClient
    coordinator: GreeVersatiDataUpdateCoordinator
    integration: Integration
