"""
In-process UDP emulator of a Gree Versati unit for protocol tests.

Implements the observable wire behavior: answers scans with a ``dev``
pack, binds with a per-device key, serves batched ``status`` requests
and applies ``cmd`` property writes.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from custom_components.gree_versati.protocol.cipher import create_cipher

MAX_STATUS_COLS = 23


class FakeVersati(asyncio.DatagramProtocol):
    """A fake Versati unit listening on an ephemeral loopback UDP port."""

    def __init__(
        self,
        mac: str = "f4911e000001",
        cipher_kind: str = "ecb",
        device_key: str = "0123456789abcdef",
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the fake unit."""
        self.mac = mac
        self.cipher_kind = cipher_kind
        self.device_key = device_key
        self.properties: dict[str, Any] = properties if properties is not None else {}
        self.received_cmds: list[dict[str, Any]] = []
        self.max_status_cols_seen = 0
        self.transport: asyncio.DatagramTransport | None = None

    async def start(self) -> tuple[str, int]:
        """Start listening; returns (ip, port)."""
        loop = asyncio.get_running_loop()
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: self, local_addr=("127.0.0.1", 0)
        )
        ip, port = self.transport.get_extra_info("sockname")[:2]
        return ip, port

    def close(self) -> None:
        """Stop listening."""
        if self.transport is not None:
            self.transport.close()

    # ------------------------------------------------------------- protocol

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle one request datagram."""
        message = json.loads(data.decode())

        if message.get("t") == "scan":
            self._reply_dev(addr)
            return

        if message.get("t") == "pack":
            generic = message.get("i") == 1
            cipher = (
                create_cipher(self.cipher_kind)
                if generic
                else create_cipher(self.cipher_kind, self.device_key)
            )
            try:
                pack = cipher.decrypt(message["pack"], message.get("tag"))
            except Exception:
                # Real units silently drop packets encrypted with the
                # wrong scheme/key (clients rely on this when probing
                # ECB first and falling back to GCM)
                return
            self._handle_pack(pack, addr)

    def _handle_pack(self, pack: dict[str, Any], addr: tuple[str, int]) -> None:
        kind = pack.get("t")
        if kind == "bind":
            self._reply(
                {"t": "bindok", "mac": self.mac, "key": self.device_key},
                addr,
                generic=True,
            )
        elif kind == "status":
            cols = pack.get("cols", [])
            self.max_status_cols_seen = max(self.max_status_cols_seen, len(cols))
            if len(cols) > MAX_STATUS_COLS:
                # Real units truncate/ignore oversized requests
                cols = cols[:MAX_STATUS_COLS]
            self._reply(
                {
                    "t": "dat",
                    "mac": self.mac,
                    "r": 200,
                    "cols": cols,
                    "dat": [self.properties.get(c) for c in cols],
                },
                addr,
                generic=False,
            )
        elif kind == "cmd":
            opts = pack.get("opt", [])
            values = pack.get("p", [])
            self.properties.update(zip(opts, values, strict=False))
            self.received_cmds.append(pack)
            self._reply(
                {"t": "res", "mac": self.mac, "r": 200, "opt": opts, "val": values},
                addr,
                generic=False,
            )

    # --------------------------------------------------------------- replies

    def _reply_dev(self, addr: tuple[str, int]) -> None:
        self._reply(
            {
                "t": "dev",
                "cid": self.mac,
                "mac": self.mac,
                "name": "FakeVersati",
                "brand": "gree",
                "model": "gree",
                "ver": "V1.0.0",
            },
            addr,
            generic=True,
        )

    def _reply(
        self, pack: dict[str, Any], addr: tuple[str, int], *, generic: bool
    ) -> None:
        cipher = (
            create_cipher(self.cipher_kind)
            if generic
            else create_cipher(self.cipher_kind, self.device_key)
        )
        payload, tag = cipher.encrypt(pack)
        message: dict[str, Any] = {
            "t": "pack",
            "i": 1 if generic else 0,
            "uid": 0,
            "cid": self.mac,
            "tcid": "",
            "pack": payload,
        }
        if tag is not None:
            message["tag"] = tag
        assert self.transport is not None
        self.transport.sendto(json.dumps(message).encode(), addr)
