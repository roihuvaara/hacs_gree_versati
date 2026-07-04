"""
AES "pack" ciphers for the Gree local UDP protocol.

Gree devices exchange JSON packets whose ``pack`` field is an encrypted,
base64-encoded JSON document. Two schemes exist in the wild:

- AES-128-ECB with PKCS7 padding (older firmware, "V1")
- AES-128-GCM with a fixed nonce and AAD, tag sent separately ("V2")

The generic keys, nonce and AAD below are public protocol constants used
by every device before a per-device key is negotiated at bind time.

Uses the ``cryptography`` package, which is already a Home Assistant core
dependency, so the integration needs no extra requirements.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CIPHER_ECB = "ecb"
CIPHER_GCM = "gcm"

GENERIC_ECB_KEY = b"a3K8Bx%2r8Y7#xDh"
GENERIC_GCM_KEY = b"{yxAHAY_Lm6pbC/<"
GCM_NONCE = b"\x54\x40\x78\x44\x49\x67\x5a\x51\x6c\x5e\x63\x13"
GCM_AAD = b"qualcomm-test"


class EcbCipher:
    """AES-128-ECB pack cipher (protocol V1)."""

    kind = CIPHER_ECB

    def __init__(self, key: str | bytes = GENERIC_ECB_KEY) -> None:
        """Initialize with a device or generic key."""
        self._key = key.encode() if isinstance(key, str) else key

    @property
    def key(self) -> str:
        """Return the key as a string."""
        return self._key.decode()

    def encrypt(self, obj: dict[str, Any]) -> tuple[str, None]:
        """Encrypt a pack dict; returns (base64 payload, no tag)."""
        padder = padding.PKCS7(128).padder()
        data = padder.update(json.dumps(obj).encode()) + padder.finalize()
        encryptor = Cipher(algorithms.AES(self._key), modes.ECB()).encryptor()  # noqa: S305
        encrypted = encryptor.update(data) + encryptor.finalize()
        return base64.b64encode(encrypted).decode(), None

    def decrypt(self, payload: str, tag: str | None = None) -> dict[str, Any]:  # noqa: ARG002
        """Decrypt a base64 pack payload into a dict."""
        decryptor = Cipher(algorithms.AES(self._key), modes.ECB()).decryptor()  # noqa: S305
        data = decryptor.update(base64.b64decode(payload)) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plain = unpadder.update(data) + unpadder.finalize()
        return json.loads(plain.decode())


class GcmCipher:
    """AES-128-GCM pack cipher (protocol V2), tag transmitted separately."""

    kind = CIPHER_GCM

    def __init__(self, key: str | bytes = GENERIC_GCM_KEY) -> None:
        """Initialize with a device or generic key."""
        self._key = key.encode() if isinstance(key, str) else key

    @property
    def key(self) -> str:
        """Return the key as a string."""
        return self._key.decode()

    def encrypt(self, obj: dict[str, Any]) -> tuple[str, str]:
        """Encrypt a pack dict; returns (base64 payload, base64 tag)."""
        encryptor = Cipher(algorithms.AES(self._key), modes.GCM(GCM_NONCE)).encryptor()
        encryptor.authenticate_additional_data(GCM_AAD)
        encrypted = encryptor.update(json.dumps(obj).encode()) + encryptor.finalize()
        return (
            base64.b64encode(encrypted).decode(),
            base64.b64encode(encryptor.tag).decode(),
        )

    def decrypt(self, payload: str, tag: str | None = None) -> dict[str, Any]:
        """Decrypt a base64 pack payload, verifying the tag when provided."""
        raw = base64.b64decode(payload)
        if tag is not None:
            decryptor = Cipher(
                algorithms.AES(self._key),
                modes.GCM(GCM_NONCE, base64.b64decode(tag)),
            ).decryptor()
            decryptor.authenticate_additional_data(GCM_AAD)
            plain = decryptor.update(raw) + decryptor.finalize()
        else:
            # Some firmwares omit the tag; decrypt without verification
            decryptor = Cipher(
                algorithms.AES(self._key), modes.GCM(GCM_NONCE)
            ).decryptor()
            decryptor.authenticate_additional_data(GCM_AAD)
            plain = decryptor.update(raw)
        return json.loads(plain.decode())


def create_cipher(kind: str, key: str | None = None) -> EcbCipher | GcmCipher:
    """Create a cipher of the given kind, with the generic key if none given."""
    if kind == CIPHER_ECB:
        return EcbCipher(key) if key else EcbCipher()
    if kind == CIPHER_GCM:
        return GcmCipher(key) if key else GcmCipher()
    error_msg = f"Unknown cipher kind: {kind}"
    raise ValueError(error_msg)
