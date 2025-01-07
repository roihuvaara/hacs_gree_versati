"""Custom types for gree_versati."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import GreeVersatiApiClient
    from .coordinator import BlueprintDataUpdateCoordinator


type GreeVersatiConfigEntry = ConfigEntry[GreeVersatiData]


@dataclass
class GreeVersatiData:
    """Data for the Blueprint integration."""

    client: GreeVersatiApiClient
    coordinator: BlueprintDataUpdateCoordinator
    integration: Integration
