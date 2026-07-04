"""
Async UDP transport for the Gree local protocol.

Devices listen on UDP port 7000 and answer each request datagram with one
(or, for scans, several) JSON response datagrams. There is no session:
every exchange is fire-and-collect with a timeout.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from .exceptions import GreeTimeoutError

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 7000


class _ExchangeProtocol(asyncio.DatagramProtocol):
    """Send one datagram and hand every reply to a callback."""

    def __init__(
        self,
        payload: bytes,
        on_datagram: Any,
    ) -> None:
        self._payload = payload
        self._on_datagram = on_datagram
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]
        self.transport.sendto(self._payload)

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = json.loads(data.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            _LOGGER.debug("Ignoring undecodable datagram from %s", addr)
            return
        self._on_datagram(message, addr)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("UDP error: %s", exc)


async def send_receive(
    ip: str,
    port: int,
    message: dict[str, Any],
    timeout: float = 5.0,  # noqa: ASYNC109 - plain deadline, no cancellation scope
) -> dict[str, Any]:
    """Send one request to a device and return its first response."""
    loop = asyncio.get_running_loop()
    response: asyncio.Future[dict[str, Any]] = loop.create_future()

    def on_datagram(msg: dict[str, Any], _addr: tuple[str, int]) -> None:
        if not response.done():
            response.set_result(msg)

    payload = json.dumps(message).encode()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _ExchangeProtocol(payload, on_datagram),
        remote_addr=(ip, port),
    )
    try:
        return await asyncio.wait_for(response, timeout)
    except TimeoutError as err:
        error_msg = f"No response from {ip}:{port} within {timeout}s"
        raise GreeTimeoutError(error_msg) from err
    finally:
        transport.close()


async def broadcast_receive(
    message: dict[str, Any],
    wait_for: float = 5.0,
    port: int = DEFAULT_PORT,
    broadcast_address: str = "255.255.255.255",
) -> list[tuple[dict[str, Any], tuple[str, int]]]:
    """Broadcast a request and collect every response until the deadline."""
    loop = asyncio.get_running_loop()
    responses: list[tuple[dict[str, Any], tuple[str, int]]] = []

    def on_datagram(msg: dict[str, Any], addr: tuple[str, int]) -> None:
        responses.append((msg, addr))

    payload = json.dumps(message).encode()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _ExchangeProtocol(payload, on_datagram),
        remote_addr=(broadcast_address, port),
        allow_broadcast=True,
    )
    try:
        await asyncio.sleep(wait_for)
    finally:
        transport.close()
    return responses
