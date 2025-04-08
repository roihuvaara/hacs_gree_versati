import asyncio
import enum
import random
from typing import Any, Dict, Optional, Set

from gree_versati.awhp_device import AwhpProps


class MockAwhpDevice:
    """Mock device class for Air-Water Heat Pump."""

    def __init__(self, device_id: str = "mock_device", device_name: str = "Mock AWHP"):
        self._properties = {}
        self._dirty: Set[str] = set()
        self.hid = f"362001000762+U-CS532AE(LT)V3.31.bin"
        self.version = "3.31"
        self.device_id = device_id
        self.device_name = device_name
        self.device_info = {"id": device_id, "name": device_name}
        self.device_cipher = True

        # Initialize with realistic default values
        self._initialize_default_properties()

    def _initialize_default_properties(self):
        """Initialize the mock with realistic default values."""
        # Temperature values (whole + decimal parts)
        self._properties[AwhpProps.T_WATER_IN_PE_W.value] = 125  # 25°C
        self._properties[AwhpProps.T_WATER_IN_PE_D.value] = 5  # 0.5
        self._properties[AwhpProps.T_WATER_OUT_PE_W.value] = 130  # 30°C
        self._properties[AwhpProps.T_WATER_OUT_PE_D.value] = 2  # 0.2
        self._properties[AwhpProps.T_OPT_WATER_W.value] = 128  # 28°C
        self._properties[AwhpProps.T_OPT_WATER_D.value] = 0  # 0.0
        self._properties[AwhpProps.HOT_WATER_TEMP_W.value] = 150  # 50°C
        self._properties[AwhpProps.HOT_WATER_TEMP_D.value] = 3  # 0.3
        self._properties[AwhpProps.REMOTE_HOME_TEMP_W.value] = 122  # 22°C
        self._properties[AwhpProps.REMOTE_HOME_TEMP_D.value] = 1  # 0.1

        # Status values
        self._properties[AwhpProps.TANK_HEATER_STATUS.value] = 1  # On
        self._properties[AwhpProps.SYSTEM_DEFROSTING_STATUS.value] = 0  # Off
        self._properties[AwhpProps.HP_HEATER_1_STATUS.value] = 1  # On
        self._properties[AwhpProps.HP_HEATER_2_STATUS.value] = 0  # Off
        self._properties[AwhpProps.AUTOMATIC_FROST_PROTECTION.value] = 1  # On

        # Settings
        self._properties[AwhpProps.POWER.value] = 1  # On
        self._properties[AwhpProps.MODE.value] = 4  # Heat mode
        self._properties[AwhpProps.COOL_TEMP_SET.value] = 18  # 18°C
        self._properties[AwhpProps.HEAT_TEMP_SET.value] = 33  # 33°C
        self._properties[AwhpProps.HOT_WATER_TEMP_SET.value] = 55  # 55°C
        self._properties[AwhpProps.TEMP_UNIT.value] = 0  # Celsius
        self._properties[AwhpProps.TEMP_REC.value] = 0
        self._properties[AwhpProps.ALL_ERR.value] = 0  # No error

        # Other settings
        self._properties[AwhpProps.COOL_AND_HOT_WATER.value] = 1  # On
        self._properties[AwhpProps.HEAT_AND_HOT_WATER.value] = 1  # On
        self._properties[AwhpProps.TEMP_REC_B.value] = 0
        self._properties[AwhpProps.COOL_HOME_TEMP_SET.value] = 24  # 24°C
        self._properties[AwhpProps.HEAT_HOME_TEMP_SET.value] = 25  # 25°C
        self._properties[AwhpProps.FAST_HEAT_WATER.value] = 0  # Off
        self._properties[AwhpProps.QUIET.value] = 0  # Off
        self._properties[AwhpProps.LEFT_HOME.value] = 0  # Off
        self._properties[AwhpProps.DISINFECT.value] = 0  # Off
        self._properties[AwhpProps.POWER_SAVE.value] = 0  # Off
        self._properties[AwhpProps.VERSATI_SERIES.value] = 0
        self._properties[AwhpProps.ROOM_HOME_TEMP_EXT.value] = 0  # Off
        self._properties[AwhpProps.HOT_WATER_EXT.value] = 0  # Off
        self._properties[AwhpProps.FOC_MOD_SWH.value] = 0  # Off
        self._properties[AwhpProps.EMEGCY.value] = 0  # Off
        self._properties[AwhpProps.HAND_FRO_SWH.value] = 0  # Off
        self._properties[AwhpProps.WATER_SYS_EXH_SWH.value] = 0  # Off
        self._properties[AwhpProps.BORD_TEST.value] = 0  # Off
        self._properties[AwhpProps.COL_COLET_SWH.value] = 0  # Off
        self._properties[AwhpProps.END_TEMP_COT_SWH.value] = 0  # Off
        self._properties[AwhpProps.MODEL_TYPE.value] = 0
        self._properties[AwhpProps.EVU.value] = 0  # Off

    def get_property(self, prop: AwhpProps) -> Any:
        """Get property value."""
        return self._properties.get(prop.value)

    def set_property(self, prop: AwhpProps, value: Any) -> None:
        """Set property value."""
        self._properties[prop.value] = value
        self._dirty.add(prop.value)

    def _get_celsius(self, whole, decimal) -> Optional[float]:
        """Helper to combine temperature values into celsius."""
        if whole is None or decimal is None:
            return None
        return whole - 100 + (decimal / 10)

    def t_water_in_pe(
        self, raw_data: Optional[Dict[str, Any]] = None
    ) -> Optional[float]:
        """Get water input temperature."""
        if raw_data:
            return self._get_celsius(
                raw_data.get(AwhpProps.T_WATER_IN_PE_W.value),
                raw_data.get(AwhpProps.T_WATER_IN_PE_D.value),
            )
        return self._get_celsius(
            self.get_property(AwhpProps.T_WATER_IN_PE_W),
            self.get_property(AwhpProps.T_WATER_IN_PE_D),
        )

    def t_water_out_pe(
        self, raw_data: Optional[Dict[str, Any]] = None
    ) -> Optional[float]:
        """Get water output temperature."""
        if raw_data:
            return self._get_celsius(
                raw_data.get(AwhpProps.T_WATER_OUT_PE_W.value),
                raw_data.get(AwhpProps.T_WATER_OUT_PE_D.value),
            )
        return self._get_celsius(
            self.get_property(AwhpProps.T_WATER_OUT_PE_W),
            self.get_property(AwhpProps.T_WATER_OUT_PE_D),
        )

    def t_opt_water(self, raw_data: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """Get optimal water temperature."""
        if raw_data:
            return self._get_celsius(
                raw_data.get(AwhpProps.T_OPT_WATER_W.value),
                raw_data.get(AwhpProps.T_OPT_WATER_D.value),
            )
        return self._get_celsius(
            self.get_property(AwhpProps.T_OPT_WATER_W),
            self.get_property(AwhpProps.T_OPT_WATER_D),
        )

    def hot_water_temp(
        self, raw_data: Optional[Dict[str, Any]] = None
    ) -> Optional[float]:
        """Get hot water temperature."""
        if raw_data:
            return self._get_celsius(
                raw_data.get(AwhpProps.HOT_WATER_TEMP_W.value),
                raw_data.get(AwhpProps.HOT_WATER_TEMP_D.value),
            )
        return self._get_celsius(
            self.get_property(AwhpProps.HOT_WATER_TEMP_W),
            self.get_property(AwhpProps.HOT_WATER_TEMP_D),
        )

    def remote_home_temp(
        self, raw_data: Optional[Dict[str, Any]] = None
    ) -> Optional[float]:
        """Get remote home temperature."""
        if raw_data:
            return self._get_celsius(
                raw_data.get(AwhpProps.REMOTE_HOME_TEMP_W.value),
                raw_data.get(AwhpProps.REMOTE_HOME_TEMP_D.value),
            )
        return self._get_celsius(
            self.get_property(AwhpProps.REMOTE_HOME_TEMP_W),
            self.get_property(AwhpProps.REMOTE_HOME_TEMP_D),
        )

    @property
    def cool_temp_set(self) -> Optional[int]:
        return self.get_property(AwhpProps.COOL_TEMP_SET)

    @cool_temp_set.setter
    def cool_temp_set(self, value: int):
        self.set_property(AwhpProps.COOL_TEMP_SET, value)

    @property
    def heat_temp_set(self) -> Optional[int]:
        return self.get_property(AwhpProps.HEAT_TEMP_SET)

    @heat_temp_set.setter
    def heat_temp_set(self, value: int):
        self.set_property(AwhpProps.HEAT_TEMP_SET, value)

    @property
    def hot_water_temp_set(self) -> Optional[int]:
        return self.get_property(AwhpProps.HOT_WATER_TEMP_SET)

    @hot_water_temp_set.setter
    def hot_water_temp_set(self, value: int):
        self.set_property(AwhpProps.HOT_WATER_TEMP_SET, value)

    @property
    def cool_and_hot_water(self) -> bool:
        return bool(self.get_property(AwhpProps.COOL_AND_HOT_WATER))

    @cool_and_hot_water.setter
    def cool_and_hot_water(self, value: bool):
        self.set_property(AwhpProps.COOL_AND_HOT_WATER, int(value))

    @property
    def heat_and_hot_water(self) -> bool:
        return bool(self.get_property(AwhpProps.HEAT_AND_HOT_WATER))

    @heat_and_hot_water.setter
    def heat_and_hot_water(self, value: bool):
        self.set_property(AwhpProps.HEAT_AND_HOT_WATER, int(value))

    @property
    def cool_home_temp_set(self) -> Optional[int]:
        return self.get_property(AwhpProps.COOL_HOME_TEMP_SET)

    @cool_home_temp_set.setter
    def cool_home_temp_set(self, value: int):
        self.set_property(AwhpProps.COOL_HOME_TEMP_SET, value)

    @property
    def heat_home_temp_set(self) -> Optional[int]:
        return self.get_property(AwhpProps.HEAT_HOME_TEMP_SET)

    @heat_home_temp_set.setter
    def heat_home_temp_set(self, value: int):
        self.set_property(AwhpProps.HEAT_HOME_TEMP_SET, value)

    @property
    def fast_heat_water(self) -> bool:
        return bool(self.get_property(AwhpProps.FAST_HEAT_WATER))

    @fast_heat_water.setter
    def fast_heat_water(self, value: bool):
        self.set_property(AwhpProps.FAST_HEAT_WATER, int(value))

    @property
    def left_home(self) -> bool:
        return bool(self.get_property(AwhpProps.LEFT_HOME))

    @left_home.setter
    def left_home(self, value: bool):
        self.set_property(AwhpProps.LEFT_HOME, int(value))

    @property
    def disinfect(self) -> bool:
        return bool(self.get_property(AwhpProps.DISINFECT))

    @disinfect.setter
    def disinfect(self, value: bool):
        self.set_property(AwhpProps.DISINFECT, int(value))

    @property
    def power_save(self) -> bool:
        return bool(self.get_property(AwhpProps.POWER_SAVE))

    @power_save.setter
    def power_save(self, value: bool):
        self.set_property(AwhpProps.POWER_SAVE, int(value))

    @property
    def versati_series(self) -> bool:
        return bool(self.get_property(AwhpProps.VERSATI_SERIES))

    @versati_series.setter
    def versati_series(self, value: bool):
        self.set_property(AwhpProps.VERSATI_SERIES, int(value))

    @property
    def room_home_temp_ext(self) -> bool:
        return bool(self.get_property(AwhpProps.ROOM_HOME_TEMP_EXT))

    @room_home_temp_ext.setter
    def room_home_temp_ext(self, value: bool):
        self.set_property(AwhpProps.ROOM_HOME_TEMP_EXT, int(value))

    @property
    def hot_water_ext(self) -> bool:
        return bool(self.get_property(AwhpProps.HOT_WATER_EXT))

    @hot_water_ext.setter
    def hot_water_ext(self, value: bool):
        self.set_property(AwhpProps.HOT_WATER_EXT, int(value))

    @property
    def foc_mod_swh(self) -> bool:
        return bool(self.get_property(AwhpProps.FOC_MOD_SWH))

    @foc_mod_swh.setter
    def foc_mod_swh(self, value: bool):
        self.set_property(AwhpProps.FOC_MOD_SWH, int(value))

    @property
    def emegcy(self) -> bool:
        return bool(self.get_property(AwhpProps.EMEGCY))

    @emegcy.setter
    def emegcy(self, value: bool):
        self.set_property(AwhpProps.EMEGCY, int(value))

    @property
    def hand_fro_swh(self) -> bool:
        return bool(self.get_property(AwhpProps.HAND_FRO_SWH))

    @hand_fro_swh.setter
    def hand_fro_swh(self, value: bool):
        self.set_property(AwhpProps.HAND_FRO_SWH, int(value))

    @property
    def water_sys_exh_swh(self) -> bool:
        return bool(self.get_property(AwhpProps.WATER_SYS_EXH_SWH))

    @water_sys_exh_swh.setter
    def water_sys_exh_swh(self, value: bool):
        self.set_property(AwhpProps.WATER_SYS_EXH_SWH, int(value))

    @property
    def tank_heater_status(self) -> bool:
        return bool(self.get_property(AwhpProps.TANK_HEATER_STATUS))

    @property
    def system_defrosting_status(self) -> bool:
        return bool(self.get_property(AwhpProps.SYSTEM_DEFROSTING_STATUS))

    @property
    def hp_heater_1_status(self) -> bool:
        return bool(self.get_property(AwhpProps.HP_HEATER_1_STATUS))

    @property
    def hp_heater_2_status(self) -> bool:
        return bool(self.get_property(AwhpProps.HP_HEATER_2_STATUS))

    @property
    def automatic_frost_protection(self) -> bool:
        return bool(self.get_property(AwhpProps.AUTOMATIC_FROST_PROTECTION))

    @property
    def temp_unit(self) -> Optional[int]:
        return self.get_property(AwhpProps.TEMP_UNIT)

    @property
    def temp_rec(self) -> Optional[int]:
        return self.get_property(AwhpProps.TEMP_REC)

    @property
    def all_err(self) -> Optional[int]:
        return self.get_property(AwhpProps.ALL_ERR)

    @property
    def temp_rec_b(self) -> Optional[int]:
        return self.get_property(AwhpProps.TEMP_REC_B)

    @property
    def quiet(self) -> bool:
        return bool(self.get_property(AwhpProps.QUIET))

    @property
    def bord_test(self) -> bool:
        return bool(self.get_property(AwhpProps.BORD_TEST))

    @property
    def col_colet_swh(self) -> bool:
        return bool(self.get_property(AwhpProps.COL_COLET_SWH))

    @property
    def end_temp_cot_swh(self) -> bool:
        return bool(self.get_property(AwhpProps.END_TEMP_COT_SWH))

    @property
    def model_type(self) -> Optional[int]:
        return self.get_property(AwhpProps.MODEL_TYPE)

    @property
    def evu(self) -> bool:
        return bool(self.get_property(AwhpProps.EVU))

    @property
    def power(self) -> bool:
        return bool(self.get_property(AwhpProps.POWER))

    @power.setter
    def power(self, value: bool):
        self.set_property(AwhpProps.POWER, int(value))

    @property
    def mode(self) -> Optional[int]:
        return self.get_property(AwhpProps.MODE)

    @mode.setter
    def mode(self, value: int):
        self.set_property(AwhpProps.MODE, int(value))

    # Simulate the async methods with non-async implementations that add realistic delays
    async def update_all_properties(self) -> None:
        """Simulate updating all device properties."""
        # Simulate network delay
        await asyncio.sleep(0.2)

        # Simulate realistic data changes
        self._simulate_temperature_changes()
        return None

    def _simulate_temperature_changes(self):
        """Simulate small random changes in temperature values."""
        # Water in temperature
        whole = self._properties[AwhpProps.T_WATER_IN_PE_W.value]
        decimal = self._properties[AwhpProps.T_WATER_IN_PE_D.value]
        temp = self._get_celsius(whole, decimal) or 25.0
        temp += random.uniform(-0.5, 0.5)  # Random fluctuation
        # Convert back to whole/decimal
        new_whole = int(temp) + 100
        new_decimal = int((temp - int(temp)) * 10)
        self._properties[AwhpProps.T_WATER_IN_PE_W.value] = new_whole
        self._properties[AwhpProps.T_WATER_IN_PE_D.value] = new_decimal

        # Water out temperature
        whole = self._properties[AwhpProps.T_WATER_OUT_PE_W.value]
        decimal = self._properties[AwhpProps.T_WATER_OUT_PE_D.value]
        temp = self._get_celsius(whole, decimal) or 30.0
        temp += random.uniform(-0.5, 0.5)  # Random fluctuation
        # Convert back to whole/decimal
        new_whole = int(temp) + 100
        new_decimal = int((temp - int(temp)) * 10)
        self._properties[AwhpProps.T_WATER_OUT_PE_W.value] = new_whole
        self._properties[AwhpProps.T_WATER_OUT_PE_D.value] = new_decimal

        # Hot water temperature
        whole = self._properties[AwhpProps.HOT_WATER_TEMP_W.value]
        decimal = self._properties[AwhpProps.HOT_WATER_TEMP_D.value]
        temp = self._get_celsius(whole, decimal) or 50.0
        temp += random.uniform(-0.3, 0.3)  # Random fluctuation
        # Convert back to whole/decimal
        new_whole = int(temp) + 100
        new_decimal = int((temp - int(temp)) * 10)
        self._properties[AwhpProps.HOT_WATER_TEMP_W.value] = new_whole
        self._properties[AwhpProps.HOT_WATER_TEMP_D.value] = new_decimal

        # Status values randomly change sometimes
        if random.random() < 0.05:  # 5% chance
            self._properties[AwhpProps.TANK_HEATER_STATUS.value] = int(
                not self.tank_heater_status
            )

        if random.random() < 0.02:  # 2% chance
            self._properties[AwhpProps.SYSTEM_DEFROSTING_STATUS.value] = int(
                not self.system_defrosting_status
            )

    async def get_all_properties(self) -> dict:
        """Get all properties in a single request and return them."""
        await self.update_all_properties()

        # Create a dictionary of all defined properties
        props = {prop.value: self.get_property(prop) for prop in AwhpProps}

        # Add calculated temperature values
        props.update(
            {
                "water_in_temp": self.t_water_in_pe(),
                "water_out_temp": self.t_water_out_pe(),
                "hot_water_temp": self.hot_water_temp(),
                "opt_water_temp": self.t_opt_water(),
                "remote_home_temp": self.remote_home_temp(),
                "power": self.power,
                "mode": self.mode,
                "heat_temp_set": self.heat_temp_set,
                "cool_temp_set": self.cool_temp_set,
                "hot_water_temp_set": self.hot_water_temp_set,
                "fast_heat_water": self.fast_heat_water,
                "tank_heater_status": self.tank_heater_status,
                "defrosting_status": self.system_defrosting_status,
                "hp_heater_1_status": self.hp_heater_1_status,
                "hp_heater_2_status": self.hp_heater_2_status,
                "frost_protection": self.automatic_frost_protection,
                "versati_series": self.versati_series,
            }
        )

        return props

    async def update_state(self, wait_for: float = 30) -> None:
        """Mock updating the internal state of the device."""
        # Simulate network delay
        await asyncio.sleep(0.2)

        # Update with some random variations
        self._simulate_temperature_changes()
        return None

    async def push_state_update(self, wait_for: float = 30) -> None:
        """Mock pushing state updates to the unit."""
        if not self._dirty:
            return

        # Simulate network delay
        await asyncio.sleep(0.2)

        # In a real device, this would push changes to the physical device
        # For the mock, we just clear the dirty set
        self._dirty.clear()
        return None

    async def bind(self) -> None:
        """Mock binding to the device."""
        self.device_cipher = True
        await asyncio.sleep(0.2)  # Simulate network delay
        return None

    def handle_state_update(self, **kwargs) -> None:
        """Handle incoming state updates."""
        # Store previous property values for comparison
        previous_properties = {k: v for k, v in self._properties.items() if k in kwargs}

        # Update properties with new values
        self._properties.update(kwargs)

        # Log property changes (in a real implementation, this would use a logger)
        for key, new_value in kwargs.items():
            old_value = previous_properties.get(key, "N/A")
            if old_value != new_value:
                print(
                    f"Property updated: {key} changed from {old_value} to {new_value}"
                )
