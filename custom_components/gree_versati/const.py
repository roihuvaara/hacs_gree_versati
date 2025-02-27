"""Constants for gree_versati."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)
LOGGER.setLevel("DEBUG")

DOMAIN = "gree_versati"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

CONF_IP = "ip"