import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT, CONF_MAC, CONF_NAME
from .const import DOMAIN, CONF_IP
from .client import GreeVersatiClient

_LOGGER = logging.getLogger(__name__)

class GreeVersatiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Gree Versati integration."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """The initial step that the user sees."""
        errors = {}
        if user_input is not None:
            client = GreeVersatiClient()
            try:
                devices = await client.run_discovery()
            except Exception as exc:
                _LOGGER.error("Error during device discovery: %s", exc)
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({}),
                    errors=errors,
                )
            
            if not devices:
                errors["base"] = "no_devices_found"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({}),
                    errors=errors,
                )

            # If exactly one device is discovered, proceed to bind immediately.
            if len(devices) == 1:
                device = devices[0]
                return await self.async_step_bind({"mac": device.device_info.mac})

            # If more than one device is found, let the user choose which one to bind.
            device_options = {
                device.device_info.mac: f"{device.name} ({device.ip})" for device in devices
            }
            return self.async_show_form(
                step_id="select_device",
                data_schema=vol.Schema({
                    vol.Required("mac"): vol.In(device_options),
                }),
                errors=errors,
            )

        # If no user input yet, display a simple form.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
        )

    async def async_step_select_device(self, user_input=None):
        """Handle device selection when multiple devices are discovered."""
        if user_input is None:
            return await self.async_step_user()
        return await self.async_step_bind(user_input)

    async def async_step_bind(self, user_input):
        """Bind to the device by negotiating the key."""
        mac = user_input.get("mac")
        if not mac:
            return self.async_abort(reason="invalid_device")
        
        client = GreeVersatiClient()
        try:
            devices = await client.run_discovery()
        except Exception as exc:
            _LOGGER.error("Error during discovery in binding step: %s", exc)
            return self.async_abort(reason="cannot_connect")
        
        device = next((d for d in devices if d.mac == mac), None)
        if device is None:
            return self.async_abort(reason="device_not_found")
        
        try:
            key = await device.bind()
        except Exception as exc:
            _LOGGER.error("Error during binding with device %s: %s", mac, exc)
            return self.async_abort(reason="bind_failed")
        
        await self.async_set_unique_id(device.device_info.mac)
        self._abort_if_unique_id_configured()
        
        config_data = {
            CONF_IP: device.ip,
            CONF_PORT: device.port,
            CONF_MAC: device.device_info.mac,
            CONF_NAME: device.name,
            "key": key,
        }
        
        return self.async_create_entry(title=device.name, data=config_data)
