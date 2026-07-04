"""
Discovery of Gree devices on the local network.

A plain-text ``{"t": "scan"}`` datagram is broadcast on UDP port 7000;
each device answers with a generic-key-encrypted ``dev`` pack carrying
its identity. Both cipher schemes are tried when decrypting, since the
scheme is not known before the first contact.
"""

from __future__ import annotations

import logging
from typing import Any

from .cipher import CIPHER_ECB, CIPHER_GCM, create_cipher
from .device import DeviceInfo
from .network import DEFAULT_PORT, broadcast_receive

_LOGGER = logging.getLogger(__name__)


def _decrypt_scan_response(message: dict[str, Any]) -> dict[str, Any] | None:
    """Decrypt a scan response pack, trying both generic ciphers."""
    pack = message.get("pack")
    if pack is None:
        return None
    for kind in (CIPHER_ECB, CIPHER_GCM):
        try:
            return create_cipher(kind).decrypt(pack, message.get("tag"))
        except Exception as err:  # noqa: BLE001 - wrong cipher shows up as garbage
            _LOGGER.debug("Scan response not decodable as %s: %s", kind, err)
    return None


async def search_devices(
    wait_for: float = 5.0,
    port: int = DEFAULT_PORT,
    broadcast_address: str = "255.255.255.255",
) -> list[DeviceInfo]:
    """Broadcast a scan and return the devices that answered."""
    _LOGGER.debug("Broadcasting device scan to %s:%s", broadcast_address, port)
    responses = await broadcast_receive(
        {"t": "scan"}, wait_for, port, broadcast_address
    )

    devices: dict[str, DeviceInfo] = {}
    for message, (ip, _) in responses:
        dev = _decrypt_scan_response(message)
        if dev is None or dev.get("t") != "dev":
            continue
        mac = dev.get("mac") or message.get("cid") or ""
        if not mac or mac in devices:
            continue
        devices[mac] = DeviceInfo(
            ip=ip,
            port=port,
            mac=mac,
            name=dev.get("name", ""),
            brand=dev.get("brand", ""),
            model=dev.get("model", ""),
            version=dev.get("ver", ""),
        )
        _LOGGER.debug("Discovered device: %s", devices[mac])

    return list(devices.values())
