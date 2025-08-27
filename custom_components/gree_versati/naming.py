"""Helpers for user-facing naming and titles."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.const import CONF_MAC, CONF_NAME

DEFAULT_NAME = "Gree Versati"


def sanitize_device_name(name: str | None, mac: str | None) -> str:
    """Return a cleaned device name without MAC/hex suffixes in parentheses."""
    if not name or not isinstance(name, str):
        return ""

    cleaned = name.strip()

    # If we have a MAC, normalize to alphanumeric for comparisons
    mac_compact = ""
    if isinstance(mac, str):
        mac_compact = "".join(ch for ch in mac if ch.isalnum()).lower()

    # Remove trailing parentheses if they contain long hex (>=8 chars) or match the MAC
    m = re.search(r"\s*\(([0-9A-Fa-f]{8,})\)\s*$", cleaned)
    if m:
        suffix = m.group(1).lower()
        if suffix == mac_compact or re.fullmatch(r"[0-9a-f]{8,}", suffix):
            cleaned = re.sub(r"\s*\([0-9A-Fa-f]{8,}\)\s*$", "", cleaned).strip()

    return cleaned


def get_entry_name(entry: Any) -> str:
    """
    Return the friendly name for a config entry.

    Preference order:
    1) entry.data[CONF_NAME] when present and non-empty
    2) entry.title when present and non-empty
    3) DEFAULT_NAME
    Applies sanitization to strip MAC/hex suffixes from discovered titles.
    """
    # Guard against tests/mocks setting entry.data to a MagicMock or non-dict
    data = getattr(entry, "data", None)
    if not isinstance(data, dict):
        data = {}

    mac = data.get(CONF_MAC)
    raw_name = data.get(CONF_NAME) or getattr(entry, "title", None)
    cleaned = sanitize_device_name(raw_name, mac)
    return cleaned or DEFAULT_NAME
