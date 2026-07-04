"""Discovery tests against the in-process emulator."""

from __future__ import annotations

import pytest

from custom_components.gree_versati.protocol import search_devices
from tests.protocol.emulator import FakeVersati

# These tests exercise real UDP sockets on loopback against the emulator
pytestmark = pytest.mark.enable_socket


@pytest.mark.asyncio
@pytest.mark.parametrize("cipher_kind", ["ecb", "gcm"])
async def test_search_finds_device(cipher_kind):
    """A scan finds the unit and decodes its identity pack."""
    unit = FakeVersati(cipher_kind=cipher_kind)
    ip, port = await unit.start()
    try:
        devices = await search_devices(wait_for=0.5, port=port, broadcast_address=ip)
        assert len(devices) == 1
        info = devices[0]
        assert info.mac == unit.mac
        assert info.ip == ip
        assert info.port == port
        assert info.name == "FakeVersati"
    finally:
        unit.close()


@pytest.mark.asyncio
async def test_search_no_devices():
    """A scan with no units around returns an empty list."""
    devices = await search_devices(
        wait_for=0.2, port=59999, broadcast_address="127.0.0.1"
    )
    assert devices == []
