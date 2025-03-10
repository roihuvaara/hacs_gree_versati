"""Custom types for gree_versati."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .client import GreeVersatiClient
    from .coordinator import GreeVersatiDataUpdateCoordinator


type GreeVersatiConfigEntry = ConfigEntry[GreeVersatiData]


@dataclass
class GreeVersatiData:
    """Data class for runtime data."""

    def __init__(
        self,
        client: GreeVersatiClient,
        coordinator: GreeVersatiDataUpdateCoordinator,
    ) -> None:
        """Initialize the data class."""
        self.client = client
        self.coordinator = coordinator
