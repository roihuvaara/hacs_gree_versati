"""Tests for the protocol pack ciphers."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidTag

from custom_components.gree_versati.protocol.cipher import (
    CIPHER_ECB,
    CIPHER_GCM,
    EcbCipher,
    GcmCipher,
    create_cipher,
)


def test_ecb_roundtrip():
    """ECB encrypt/decrypt roundtrips a pack dict."""
    cipher = EcbCipher()
    payload, tag = cipher.encrypt({"t": "bind", "mac": "aabbcc", "uid": 0})
    assert tag is None
    assert cipher.decrypt(payload) == {"t": "bind", "mac": "aabbcc", "uid": 0}


def test_ecb_roundtrip_device_key():
    """ECB works with a negotiated 16-char device key."""
    cipher = EcbCipher("0123456789abcdef")
    payload, _ = cipher.encrypt({"t": "status", "cols": ["Pow", "Mod"]})
    assert cipher.decrypt(payload)["cols"] == ["Pow", "Mod"]


def test_gcm_roundtrip_with_tag():
    """GCM encrypt produces a tag that decrypt verifies."""
    cipher = GcmCipher()
    payload, tag = cipher.encrypt({"t": "dev", "mac": "aabbcc"})
    assert tag is not None
    assert cipher.decrypt(payload, tag) == {"t": "dev", "mac": "aabbcc"}


def test_gcm_wrong_tag_rejected():
    """A corrupted GCM tag fails verification."""
    cipher = GcmCipher()
    payload, tag = cipher.encrypt({"t": "dev"})
    bad_tag = ("A" + tag[1:]) if tag[0] != "A" else ("B" + tag[1:])
    with pytest.raises(InvalidTag):
        cipher.decrypt(payload, bad_tag)


def test_gcm_decrypt_without_tag():
    """Decryption without a tag is tolerated (some firmwares omit it)."""
    cipher = GcmCipher()
    payload, _ = cipher.encrypt({"t": "dat", "cols": ["Pow"], "dat": [1]})
    assert cipher.decrypt(payload) == {"t": "dat", "cols": ["Pow"], "dat": [1]}


def test_create_cipher_kinds_and_generic_keys():
    """Factory returns the right kind with generic keys by default."""
    ecb = create_cipher(CIPHER_ECB)
    gcm = create_cipher(CIPHER_GCM)
    assert isinstance(ecb, EcbCipher)
    assert isinstance(gcm, GcmCipher)
    assert ecb.key == "a3K8Bx%2r8Y7#xDh"
    assert gcm.key == "{yxAHAY_Lm6pbC/<"


def test_create_cipher_with_key():
    """Factory applies a provided device key."""
    cipher = create_cipher(CIPHER_ECB, "0123456789abcdef")
    assert cipher.key == "0123456789abcdef"


def test_create_cipher_unknown_kind():
    """Unknown kinds are rejected."""
    with pytest.raises(ValueError, match="Unknown cipher kind"):
        create_cipher("rot13")
