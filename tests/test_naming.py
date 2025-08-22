"""Tests for user-facing names and titles."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PORT

from custom_components.gree_versati.config_flow import GreeVersatiConfigFlow
from custom_components.gree_versati.const import CONF_IP
from custom_components.gree_versati.entity import GreeVersatiEntity


class TestNaming:
    """Validate naming behavior across the integration."""

    @pytest.mark.asyncio
    async def test_config_flow_sets_conf_name_fallback_when_missing(self, hass):
        """If discovered device has no name, CONF_NAME should be a friendly fallback, not None."""
        flow = GreeVersatiConfigFlow()
        flow.hass = hass
        # Avoid uniqueness side effects in tests
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock(return_value=None)

        # Build a fake discovered device with no name
        device_info = SimpleNamespace(
            ip="192.0.2.1", port=7000, mac="AA:BB:CC:DD:EE:FF", name=None
        )

        async def fake_bind():
            return "test-key"

        device = SimpleNamespace(
            device_info=device_info, bind=AsyncMock(side_effect=fake_bind)
        )

        with patch(
            "custom_components.gree_versati.config_flow.GreeVersatiClient.run_discovery",
            new=AsyncMock(return_value=[device]),
        ):
            # Trigger user step with discovery (no user_input)
            result = await flow.async_step_user(user_input={})

        assert result["type"] == "create_entry"
        # The data should include a non-empty CONF_NAME, not None
        assert result["data"][CONF_NAME] is not None
        assert isinstance(result["data"][CONF_NAME], str)
        assert result["data"][CONF_NAME].strip()

    def test_entity_device_info_uses_conf_name_not_title(self):
        """DeviceInfo.name should use CONF_NAME from entry data, not the entry title."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "abc123"
        coordinator.config_entry.title = "Generic Title"
        coordinator.config_entry.data = {
            CONF_NAME: "Friendly Name",
            CONF_IP: "192.0.2.2",
            CONF_PORT: 7000,
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        }
        coordinator.config_entry.runtime_data.client = MagicMock()
        coordinator.config_entry.runtime_data.client.mac = "AA:BB:CC:DD:EE:FF"
        coordinator.data = {"versati_series": "III"}

        entity = GreeVersatiEntity(coordinator)
        info = entity.device_info

        assert info is not None
        assert info.get("name") == "Friendly Name"
