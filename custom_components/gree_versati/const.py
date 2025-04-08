"""Constants for the Gree Versati integration."""

from __future__ import annotations

import logging
from typing import Final

LOGGER: Final = logging.getLogger(__name__)
ATTRIBUTION: Final = "Data provided by jsonplaceholder.typicode.com"
DOMAIN: Final = "gree_versati"

# Configuration
CONF_IP: Final = "ip"
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_MAC: Final = "mac"
CONF_DEVICE_NAME: Final = "device_name"
CONF_BIND_KEY: Final = "bind_key"

# Platforms
PLATFORMS: Final = ["climate", "select"]

# Operating modes
HEAT_MODE: Final = "heat"
COOL_MODE: Final = "cool"
HEAT_DHW_MODE: Final = "heat_dhw"
COOL_DHW_MODE: Final = "cool_dhw"

# Water heater operation modes
OPERATION_LIST = ["normal", "performance"]

# Configuration options
CONF_EXTERNAL_TEMP_SENSOR = "external_temp_sensor"
CONF_USE_WATER_TEMP_AS_CURRENT = "use_water_temp_as_current"
