"""Adds config flow for Gree Versati."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class GreeVersatiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Gree Versati."""

    VERSION = 1

    async def async_step_noop(
        self,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow."""
        _errors = {}
        return self.async_show_form(
            step_id="noop",
            data_schema=vol.Schema({}),
            errors=_errors,
        )
