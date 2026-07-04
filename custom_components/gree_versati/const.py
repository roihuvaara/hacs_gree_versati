"""Constants for gree_versati."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "gree_versati"

CONF_IP = "ip"

# Device "Mod" property values (Versati AWHP table, verified against
# ha-gree-versati3 and the Versati III Modbus register map — NOT the
# Gree AC table where 1=cool/4=heat).
MODE_HEAT = 1
MODE_HOT_WATER = 2
MODE_COOL_HOT_WATER = 3
MODE_HEAT_HOT_WATER = 4
MODE_COOL = 5

HEATING_MODES = {MODE_HEAT, MODE_HEAT_HOT_WATER}
COOLING_MODES = {MODE_COOL, MODE_COOL_HOT_WATER}
DHW_MODES = {MODE_HOT_WATER, MODE_COOL_HOT_WATER, MODE_HEAT_HOT_WATER}

# Logical device modes accepted by GreeVersatiClient.set_device_mode,
# mapped to the Mod value to write (None = power off, Mod untouched).
DEVICE_MODE_TO_MOD = {
    "off": None,
    "heat": MODE_HEAT,
    "hot_water": MODE_HOT_WATER,
    "cool_hot_water": MODE_COOL_HOT_WATER,
    "heat_hot_water": MODE_HEAT_HOT_WATER,
    "cool": MODE_COOL,
}
MOD_TO_DEVICE_MODE = {
    mod: name for name, mod in DEVICE_MODE_TO_MOD.items() if mod is not None
}

# Setpoint limits (°C), verified against the device's own controls
HEAT_TEMP_MIN = 20
HEAT_TEMP_MAX = 60
COOL_TEMP_MIN = 7
COOL_TEMP_MAX = 25
DHW_TEMP_MIN = 40
DHW_TEMP_MAX = 80

# Water heater operation modes. Values match HA's water_heater state
# strings (STATE_OFF / STATE_HEAT_PUMP / STATE_PERFORMANCE).
# "off": no DHW in the device mode; "heat_pump": normal DHW;
# "performance": DHW with the FastHtWter boost flag set.
OPERATION_MODE_OFF = "off"
OPERATION_MODE_HEAT_PUMP = "heat_pump"
OPERATION_MODE_PERFORMANCE = "performance"
OPERATION_LIST = [
    OPERATION_MODE_OFF,
    OPERATION_MODE_HEAT_PUMP,
    OPERATION_MODE_PERFORMANCE,
]
