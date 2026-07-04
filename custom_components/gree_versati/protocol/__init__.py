"""
Clean-room implementation of the Gree local UDP protocol (AWHP units only).

Written from publicly documented protocol facts (packet shapes, generic
keys, property names) — MIT licensed, no code derived from GPL sources.
"""

from .cipher import CIPHER_ECB, CIPHER_GCM, EcbCipher, GcmCipher, create_cipher
from .device import AwhpDevice, AwhpProps, DeviceInfo
from .discovery import search_devices
from .exceptions import (
    GreeBindError,
    GreeProtocolError,
    GreeTimeoutError,
)

__all__ = [
    "CIPHER_ECB",
    "CIPHER_GCM",
    "AwhpDevice",
    "AwhpProps",
    "DeviceInfo",
    "EcbCipher",
    "GcmCipher",
    "GreeBindError",
    "GreeProtocolError",
    "GreeTimeoutError",
    "create_cipher",
    "search_devices",
]
