"""Configuration flow for Gree Versati integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .client import GreeVersatiClient
from .const import (
    CONF_COOL_TEMP_MAX,
    CONF_COOL_TEMP_MIN,
    CONF_DHW_TEMP_MAX,
    CONF_DHW_TEMP_MIN,
    CONF_HEAT_TEMP_MAX,
    CONF_HEAT_TEMP_MIN,
    CONF_IP,
    COOL_TEMP_MAX,
    COOL_TEMP_MIN,
    DHW_TEMP_MAX,
    DHW_TEMP_MIN,
    DOMAIN,
    HEAT_TEMP_MAX,
    HEAT_TEMP_MIN,
)
from .naming import sanitize_device_name

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

_LOGGER = logging.getLogger(__name__)


def _temperature_selector(low: int, high: int) -> NumberSelector:
    """Build a °C number box limited to the device's own range."""
    return NumberSelector(
        NumberSelectorConfig(
            min=low,
            max=high,
            step=1,
            unit_of_measurement="°C",
            mode=NumberSelectorMode.BOX,
        )
    )


class GreeVersatiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Gree Versati integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,  # noqa: ARG004
    ) -> GreeVersatiOptionsFlow:
        """Create the options flow."""
        return GreeVersatiOptionsFlow()

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
                    def _label(d: Any) -> str:
                        name = d.device_info.name or "Gree Versati"
                        mac = d.device_info.mac or ""
                        # Append last 4 alphanumeric chars from MAC for disambiguation
                        mac_compact = "".join(ch for ch in mac.upper() if ch.isalnum())
                        last4 = mac_compact[-4:]
                        suffix = f" · {last4}" if last4 else ""
                        return f"{name}{suffix}"

                    device_options = {
                        d.device_info.mac: _label(d)
                        for d in devices
                        if d.device_info is not None
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

        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        # Use a friendly non-empty name and sanitize hex/MAC
        # suffix if present
        friendly_name = (
            sanitize_device_name(device.device_info.name, device.device_info.mac)
            or "Gree Versati"
        )

        return self.async_create_entry(
            title=friendly_name,
            data={
                CONF_IP: device.device_info.ip,
                CONF_PORT: device.device_info.port,
                CONF_MAC: device.device_info.mac,
                CONF_NAME: friendly_name,
                "key": key,
                "cipher_type": device.cipher_type,
            },
        )


# (option key, device min, device max) for each configurable setpoint range
_LIMIT_RANGES = [
    (CONF_HEAT_TEMP_MIN, CONF_HEAT_TEMP_MAX, HEAT_TEMP_MIN, HEAT_TEMP_MAX, "heat"),
    (CONF_COOL_TEMP_MIN, CONF_COOL_TEMP_MAX, COOL_TEMP_MIN, COOL_TEMP_MAX, "cool"),
    (CONF_DHW_TEMP_MIN, CONF_DHW_TEMP_MAX, DHW_TEMP_MIN, DHW_TEMP_MAX, "dhw"),
]


class GreeVersatiOptionsFlow(config_entries.OptionsFlow):
    """Options flow for tightening the settable temperature ranges."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the temperature limit options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # NumberSelector returns floats; store whole degrees
            data = {key: int(value) for key, value in user_input.items()}
            for min_key, max_key, _, _, label in _LIMIT_RANGES:
                if data[min_key] > data[max_key]:
                    errors["base"] = f"{label}_min_above_max"
                    break
            else:
                return self.async_create_entry(title="", data=data)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    key,
                    default=options.get(key, default),
                ): _temperature_selector(low, high)
                for min_key, max_key, low, high, _ in _LIMIT_RANGES
                for key, default in ((min_key, low), (max_key, high))
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
