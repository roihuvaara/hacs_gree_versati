"""Minimal test fixtures for testing."""

import os
import sys
import pytest

# Add the repository root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from custom_components.gree_versati.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Disable the auto_enable_custom_integrations fixture
# @pytest.fixture(autouse=True)
# def auto_enable_custom_integrations(enable_custom_integrations):
#     """Enable custom integrations defined in the test directory."""
#     yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 7000,
            "name": "Test Gree Versati",
            "mac": "AA:BB:CC:DD:EE:FF",
            "key": "test_key",
            "ip": "192.168.1.100",
        },
        entry_id="test",
    )
