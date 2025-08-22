"""Helpers for user-facing naming and titles."""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_NAME

DEFAULT_NAME = "Gree Versati"


def get_entry_name(entry: Any) -> str:
    """
    Return the friendly name for a config entry.

    Preference order:
    1) entry.data[CONF_NAME] when present and non-empty
    2) entry.title when present and non-empty
    3) DEFAULT_NAME
    """
    # Guard against tests/mocks setting entry.data to a MagicMock or non-dict
    data = getattr(entry, "data", None)
    if not isinstance(data, dict):
        data = {}
    data_name = data.get(CONF_NAME)

    return data_name or getattr(entry, "title", None) or DEFAULT_NAME
