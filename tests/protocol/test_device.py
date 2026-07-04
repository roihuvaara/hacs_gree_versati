"""End-to-end protocol tests against the in-process Versati emulator."""

from __future__ import annotations

import pytest

from custom_components.gree_versati.protocol import (
    AwhpDevice,
    AwhpProps,
    DeviceInfo,
    GreeBindError,
)
from tests.protocol.emulator import MAX_STATUS_COLS, FakeVersati

# These tests exercise real UDP sockets on loopback against the emulator
pytestmark = pytest.mark.enable_socket


def _device_for(unit: FakeVersati, ip: str, port: int, **kwargs: object) -> AwhpDevice:
    return AwhpDevice(
        DeviceInfo(ip=ip, port=port, mac=unit.mac),
        timeout=2.0,
        **kwargs,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("cipher_kind", ["ecb", "gcm"])
async def test_bind_negotiates_key_and_cipher(cipher_kind):
    """Fresh bind negotiates the key and detects the cipher scheme."""
    unit = FakeVersati(cipher_kind=cipher_kind)
    ip, port = await unit.start()
    try:
        device = _device_for(unit, ip, port)
        key = await device.bind()
        assert key == unit.device_key
        assert device.cipher_type == cipher_kind
    finally:
        unit.close()


@pytest.mark.asyncio
async def test_bind_with_stored_key_is_noop():
    """A stored key + cipher type short-circuits binding."""
    device = AwhpDevice(
        DeviceInfo(ip="127.0.0.1", port=1, mac="dead"),  # nothing listens here
        key="storedkey",
        cipher_type="ecb",
        timeout=0.5,
    )
    assert await device.bind() == "storedkey"


@pytest.mark.asyncio
async def test_bind_failure_raises():
    """No answer on either cipher raises GreeBindError."""
    device = AwhpDevice(
        DeviceInfo(ip="127.0.0.1", port=1, mac="dead"),
        timeout=0.2,
    )
    with pytest.raises(GreeBindError):
        await device.bind()


@pytest.mark.asyncio
@pytest.mark.parametrize("cipher_kind", ["ecb", "gcm"])
async def test_get_all_properties_batched(cipher_kind):
    """All props are fetched in <=23-column batches and merged."""
    unit = FakeVersati(
        cipher_kind=cipher_kind,
        properties={
            "Pow": 1,
            "Mod": 4,
            "HeWatOutTemSet": 42,
            "AllOutWatTemHi": 145,
            "AllOutWatTemLo": 5,
        },
    )
    ip, port = await unit.start()
    try:
        device = _device_for(unit, ip, port)
        data = await device.get_all_properties()

        assert data["Pow"] == 1
        assert data["Mod"] == 4
        assert data["HeWatOutTemSet"] == 42
        # Batching respected the device's column limit
        assert unit.max_status_cols_seen <= MAX_STATUS_COLS
        # Split temperature pair combines to celsius
        assert device.t_water_out_pe(data) == 45.5
    finally:
        unit.close()


@pytest.mark.asyncio
async def test_push_state_update_sends_dirty_props():
    """Staged writes go out as one cmd; booleans become ints on the wire."""
    unit = FakeVersati(properties={"Pow": 0, "Mod": 1})
    ip, port = await unit.start()
    try:
        device = _device_for(unit, ip, port)
        await device.bind()

        device.set_property(AwhpProps.MODE, 4)
        device.set_property(AwhpProps.POWER, value=True)
        await device.push_state_update()

        assert len(unit.received_cmds) == 1
        cmd = unit.received_cmds[0]
        assert cmd["opt"] == ["Mod", "Pow"]
        assert cmd["p"] == [4, 1]
        assert unit.properties["Mod"] == 4
        assert unit.properties["Pow"] == 1
    finally:
        unit.close()


@pytest.mark.asyncio
async def test_push_state_update_noop_when_clean():
    """No dirty props means no datagram at all."""
    unit = FakeVersati()
    ip, port = await unit.start()
    try:
        device = _device_for(unit, ip, port)
        await device.bind()
        await device.push_state_update()
        assert unit.received_cmds == []
    finally:
        unit.close()


@pytest.mark.asyncio
async def test_set_property_skips_unchanged_value():
    """Setting the cached value again does not mark it dirty."""
    unit = FakeVersati(properties={"Pow": 1})
    ip, port = await unit.start()
    try:
        device = _device_for(unit, ip, port)
        await device.get_all_properties()

        device.set_property(AwhpProps.POWER, 1)
        await device.push_state_update()
        assert unit.received_cmds == []
    finally:
        unit.close()


@pytest.mark.asyncio
async def test_temp_helpers_return_none_when_missing():
    """Split-temp helpers return None for absent values."""
    device = AwhpDevice(DeviceInfo(ip="127.0.0.1", port=1, mac="dead"))
    assert device.t_water_out_pe({}) is None
    assert device.hot_water_temp({"WatBoxTemHi": 150}) is None
