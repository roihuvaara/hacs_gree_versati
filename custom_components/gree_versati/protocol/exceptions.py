"""Exceptions for the Gree local protocol."""


class GreeProtocolError(Exception):
    """Base error for Gree protocol failures."""


class GreeTimeoutError(GreeProtocolError):
    """The device did not answer within the timeout."""


class GreeBindError(GreeProtocolError):
    """Binding/key negotiation with the device failed."""
