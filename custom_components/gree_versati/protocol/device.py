"""
Gree Versati (AWHP) device: bind, poll and command over the local protocol.

Property names are protocol facts observed on Versati units. Temperatures
are reported as split values: a whole part offset by +100 (``...TemHi``)
and a decimal digit (``...TemLo``), so 45.5 °C arrives as Hi=145, Lo=5.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any

from .cipher import CIPHER_ECB, CIPHER_GCM, EcbCipher, GcmCipher, create_cipher
from .exceptions import GreeBindError, GreeProtocolError, GreeTimeoutError
from .network import send_receive

_LOGGER = logging.getLogger(__name__)

# The unit truncates status responses with too many columns; two batches
# of up to 23 cover the full AwhpProps set reliably.
STATUS_BATCH_SIZE = 23


@dataclass
class DeviceInfo:
    """Connection and identity info for a device on the LAN."""

    ip: str
    port: int
    mac: str
    name: str = ""
    brand: str = ""
    model: str = ""
    version: str = ""

    def __str__(self) -> str:
        """Return a readable identity string."""
        return f"{self.name or self.mac} @ {self.ip}:{self.port}"


class AwhpProps(enum.Enum):
    """Property names exposed by Versati air-to-water heat pumps."""

    # Temperatures (split whole/decimal pairs, see module docstring)
    T_WATER_IN_PE_W = "AllInWatTemHi"
    T_WATER_IN_PE_D = "AllInWatTemLo"
    T_WATER_OUT_PE_W = "AllOutWatTemHi"
    T_WATER_OUT_PE_D = "AllOutWatTemLo"
    T_OPT_WATER_W = "HepOutWatTemHi"
    T_OPT_WATER_D = "HepOutWatTemLo"
    HOT_WATER_TEMP_W = "WatBoxTemHi"
    HOT_WATER_TEMP_D = "WatBoxTemLo"
    REMOTE_HOME_TEMP_W = "RmoHomTemHi"
    REMOTE_HOME_TEMP_D = "RmoHomTemLo"

    # Status indicators
    TANK_HEATER_STATUS = "WatBoxElcHeRunSta"
    SYSTEM_DEFROSTING_STATUS = "SyAnFroRunSta"
    HP_HEATER_1_STATUS = "ElcHe1RunSta"
    HP_HEATER_2_STATUS = "ElcHe2RunSta"
    AUTOMATIC_FROST_PROTECTION = "AnFrzzRunSta"

    # Core settings
    POWER = "Pow"
    MODE = "Mod"
    COOL_TEMP_SET = "CoWatOutTemSet"
    HEAT_TEMP_SET = "HeWatOutTemSet"
    HOT_WATER_TEMP_SET = "WatBoxTemSet"
    TEMP_UNIT = "TemUn"
    TEMP_REC = "TemRec"
    ALL_ERR = "AllErr"

    # Combined-mode helpers and home temperature setpoints
    COOL_AND_HOT_WATER = "ColHtWter"
    HEAT_AND_HOT_WATER = "HetHtWter"
    TEMP_REC_B = "TemRecB"
    COOL_HOME_TEMP_SET = "CoHomTemSet"
    HEAT_HOME_TEMP_SET = "HeHomTemSet"

    # Feature flags
    FAST_HEAT_WATER = "FastHtWter"
    QUIET = "Quiet"
    LEFT_HOME = "LefHom"
    DISINFECT = "SwDisFct"
    POWER_SAVE = "SvSt"
    VERSATI_SERIES = "VersatiSeries"
    ROOM_HOME_TEMP_EXT = "RomHomTemExt"
    HOT_WATER_EXT = "WatBoxExt"
    FOC_MOD_SWH = "FocModSwh"
    EMEGCY = "Emegcy"
    HAND_FRO_SWH = "HanFroSwh"
    WATER_SYS_EXH_SWH = "WatSyExhSwh"
    BORD_TEST = "BordTest"
    COL_COLET_SWH = "ColColetSwh"
    END_TEMP_COT_SWH = "EndTemCotSwh"
    MODEL_TYPE = "ModelType"
    EVU = "EVU"


def _split_temp_to_celsius(
    whole: float | None, decimal: float | None
) -> float | None:
    """Combine a Hi/Lo temperature pair into celsius."""
    if whole is None or decimal is None:
        return None
    return whole - 100 + decimal / 10


@dataclass
class AwhpDevice:
    """A bound (or bindable) Versati unit on the LAN."""

    device_info: DeviceInfo
    key: str | None = None
    cipher_type: str | None = None
    timeout: float = 10.0
    _properties: dict[str, Any] = field(default_factory=dict)
    _dirty: list[str] = field(default_factory=list)

    @property
    def raw_properties(self) -> dict[str, Any]:
        """Return the last known raw property values."""
        return self._properties

    # ---------------------------------------------------------------- crypto

    def _device_cipher(self) -> EcbCipher | GcmCipher:
        if self.key is None or self.cipher_type is None:
            error_msg = "Device is not bound (no key/cipher negotiated)"
            raise GreeBindError(error_msg)
        return create_cipher(self.cipher_type, self.key)

    async def _request(
        self,
        pack: dict[str, Any],
        cipher: EcbCipher | GcmCipher,
        *,
        generic: bool = False,
    ) -> dict[str, Any]:
        """Send an encrypted pack and return the decrypted response pack."""
        payload, tag = cipher.encrypt(pack)
        message: dict[str, Any] = {
            "cid": "app",
            # i=1 marks generic-key encryption, i=0 the device key
            "i": 1 if generic else 0,
            "t": "pack",
            "uid": 0,
            "tcid": self.device_info.mac,
            "pack": payload,
        }
        if tag is not None:
            message["tag"] = tag

        response = await send_receive(
            self.device_info.ip, self.device_info.port, message, self.timeout
        )
        return self._decrypt_response(response, cipher)

    def _decrypt_response(
        self, message: dict[str, Any], request_cipher: EcbCipher | GcmCipher
    ) -> dict[str, Any]:
        """Decrypt the pack of a response message."""
        if "pack" not in message:
            return message
        # Responses flagged i=1 (bind, scan) are generic-key encrypted;
        # everything else uses the same cipher as the request.
        if message.get("i") == 1:
            cipher: EcbCipher | GcmCipher = create_cipher(request_cipher.kind)
        else:
            cipher = request_cipher
        return cipher.decrypt(message["pack"], message.get("tag"))

    # ------------------------------------------------------------------ bind

    async def bind(self) -> str:
        """
        Ensure a device key: negotiate one if needed, return it.

        A fresh bind tries ECB first, then GCM, remembering which scheme
        the unit answered with. With a stored key this is a no-op.
        """
        if self.key is not None and self.cipher_type is not None:
            return self.key

        kinds = [self.cipher_type] if self.cipher_type else [CIPHER_ECB, CIPHER_GCM]
        pack = {"mac": self.device_info.mac, "t": "bind", "uid": 0}
        last_error: Exception | None = None

        for kind in kinds:
            try:
                response = await self._request(
                    pack, create_cipher(kind), generic=True
                )
            except (GreeTimeoutError, GreeProtocolError, ValueError) as err:
                _LOGGER.debug("Bind with %s cipher failed: %s", kind, err)
                last_error = err
                continue

            if response.get("t") == "bindok" and response.get("key"):
                self.key = response["key"]
                self.cipher_type = kind
                _LOGGER.debug(
                    "Bound to %s using %s cipher", self.device_info, kind
                )
                return self.key

            _LOGGER.debug("Unexpected bind response: %s", response)

        error_msg = f"Could not bind to {self.device_info}"
        raise GreeBindError(error_msg) from last_error

    # ---------------------------------------------------------------- status

    async def get_all_properties(self) -> dict[str, Any]:
        """Poll all known properties (batched) and return name -> value."""
        await self.bind()
        cipher = self._device_cipher()
        names = [prop.value for prop in AwhpProps]

        for start in range(0, len(names), STATUS_BATCH_SIZE):
            batch = names[start : start + STATUS_BATCH_SIZE]
            pack = {"mac": self.device_info.mac, "t": "status", "cols": batch}
            response = await self._request(pack, cipher)
            cols = response.get("cols", [])
            values = response.get("dat", [])
            self._properties.update(zip(cols, values, strict=False))

        return {name: self._properties.get(name) for name in names}

    def get_property(self, prop: AwhpProps) -> Any:
        """Return the last known value of a property."""
        return self._properties.get(prop.value)

    def set_property(self, prop: AwhpProps, value: Any = None) -> None:
        """Stage a property change for the next push_state_update."""
        if self._properties.get(prop.value) == value:
            return
        self._properties[prop.value] = value
        if prop.value not in self._dirty:
            self._dirty.append(prop.value)

    async def push_state_update(self) -> None:
        """Send all staged property changes to the unit as one command."""
        if not self._dirty:
            return
        await self.bind()
        cipher = self._device_cipher()

        names = list(self._dirty)
        values = [
            int(self._properties[name])
            if isinstance(self._properties[name], bool)
            else self._properties[name]
            for name in names
        ]
        self._dirty.clear()

        pack = {
            "mac": self.device_info.mac,
            "t": "cmd",
            "opt": names,
            "p": values,
        }
        _LOGGER.debug("Pushing state update %s to %s", pack, self.device_info)
        await self._request(pack, cipher)

    # ------------------------------------------------------ temperature help

    def _pair(
        self,
        whole_prop: AwhpProps,
        decimal_prop: AwhpProps,
        raw_data: dict[str, Any] | None,
    ) -> float | None:
        source = raw_data if raw_data is not None else self._properties
        return _split_temp_to_celsius(
            source.get(whole_prop.value), source.get(decimal_prop.value)
        )

    def t_water_in_pe(
        self, raw_data: dict[str, Any] | None = None
    ) -> float | None:
        """Water inlet temperature in celsius."""
        return self._pair(
            AwhpProps.T_WATER_IN_PE_W, AwhpProps.T_WATER_IN_PE_D, raw_data
        )

    def t_water_out_pe(
        self, raw_data: dict[str, Any] | None = None
    ) -> float | None:
        """Water outlet temperature in celsius."""
        return self._pair(
            AwhpProps.T_WATER_OUT_PE_W, AwhpProps.T_WATER_OUT_PE_D, raw_data
        )

    def t_opt_water(self, raw_data: dict[str, Any] | None = None) -> float | None:
        """Heat-exchanger outlet water temperature in celsius."""
        return self._pair(
            AwhpProps.T_OPT_WATER_W, AwhpProps.T_OPT_WATER_D, raw_data
        )

    def hot_water_temp(
        self, raw_data: dict[str, Any] | None = None
    ) -> float | None:
        """DHW tank temperature in celsius."""
        return self._pair(
            AwhpProps.HOT_WATER_TEMP_W, AwhpProps.HOT_WATER_TEMP_D, raw_data
        )

    def remote_home_temp(
        self, raw_data: dict[str, Any] | None = None
    ) -> float | None:
        """Remote room sensor temperature in celsius."""
        return self._pair(
            AwhpProps.REMOTE_HOME_TEMP_W, AwhpProps.REMOTE_HOME_TEMP_D, raw_data
        )
