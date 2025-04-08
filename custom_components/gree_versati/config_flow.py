"""Configuration flow for Gree Versati integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.helpers import selector

from .client import GreeVersatiClient
from .const import (
    CONF_EXTERNAL_TEMP_SENSOR,
    CONF_IP,
    CONF_USE_WATER_TEMP_AS_CURRENT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GreeVersatiOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Gree Versati options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        options = self.config_entry.options.copy()

        if user_input is not None:
            # Update options
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        # Prepare form with current or default values
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_EXTERNAL_TEMP_SENSOR,
                        default=options.get(CONF_EXTERNAL_TEMP_SENSOR, ""),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["sensor", "number", "input_number"]
                        )
                    ),
                    vol.Optional(
                        CONF_USE_WATER_TEMP_AS_CURRENT,
                        default=options.get(CONF_USE_WATER_TEMP_AS_CURRENT, False),
                    ): bool,
                }
            ),
            errors=errors,
        )


class GreeVersatiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Gree Versati integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GreeVersatiOptionsFlowHandler:
        """Get the options flow for this handler."""
        return GreeVersatiOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the configuration flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("mac"):
                return await self.async_step_bind(user_input)

            try:
                client = GreeVersatiClient()
                devices = await client.run_discovery()
                if not devices:
                    errors["base"] = "no_devices_found"
                else:
                    # If exactly one device is discovered, proceed to bind immediately
                    if len(devices) == 1:
                        device = devices[0]
                        if device.device_info is None:
                            errors["base"] = "invalid_device"
                            return self.async_show_form(
                                step_id="user",
                                data_schema=vol.Schema({}),
                                errors=errors,
                            )
                        return await self.async_step_bind(
                            {"mac": device.device_info.mac}
                        )

                    # If more than one device is found, let the user choose which one
                    # to bind
                    device_options = {
                        device.device_info.mac: (
                            f"{device.device_info.name} ({device.device_info.mac})"
                        )
                        for device in devices
                        if device.device_info is not None
                    }
                    return self.async_show_form(
                        step_id="select_device",
                        data_schema=vol.Schema(
                            {
                                vol.Required("mac"): vol.In(device_options),
                            }
                        ),
                        errors=errors,
                    )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to discover devices")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device selection when multiple devices are discovered."""
        if user_input is None:
            return await self.async_step_user()
        return await self.async_step_bind(user_input)

    async def async_step_bind(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Handle binding to a device."""
        mac = user_input.get("mac")
        if not mac:
            return self.async_abort(reason="invalid_device")

        client = GreeVersatiClient()
        try:
            devices = await client.run_discovery()
        except Exception:
            _LOGGER.exception("Error during discovery in binding step")
            return self.async_abort(reason="cannot_connect")

        device = next(
            (
                d
                for d in devices
                if d.device_info is not None and d.device_info.mac == mac
            ),
            None,
        )
        if device is None or device.device_info is None:
            return self.async_abort(reason="device_not_found")

        try:
            key = await device.bind()
        except Exception:
            _LOGGER.exception("Error during binding with device %s", mac)
            return self.async_abort(reason="bind_failed")

        # Set a consistent unique ID for the device
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        # Use a default title if device name is not available
        device_name = device.device_info.name
        if not device_name or device_name == mac:
            device_name = f"Gree Versati ({mac})"
        else:
            # If we have a device name but it's not informative, add the MAC
            device_name = f"{device_name} ({mac})"

        return self.async_create_entry(
            title=device_name,
            data={
                CONF_IP: device.device_info.ip,
                CONF_PORT: device.device_info.port,
                CONF_MAC: device.device_info.mac,
                CONF_NAME: device_name,
                "key": key,
            },
        )
