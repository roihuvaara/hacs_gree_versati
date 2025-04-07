"""Constants for gree_versati."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)
LOGGER.setLevel("DEBUG")

DOMAIN = "gree_versati"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

CONF_IP = "ip"

# HVAC mode constants
HEAT_MODE = 4
COOL_MODE = 1

# Water heater operation modes
OPERATION_LIST = ["normal", "performance"]
