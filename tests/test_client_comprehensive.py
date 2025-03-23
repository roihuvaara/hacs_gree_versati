"""Comprehensive tests for the GreeVersatiClient class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from gree_versati.awhp_device import AwhpProps

from custom_components.gree_versati.client import GreeVersatiClient
from custom_components.gree_versati.const import COOL_MODE, HEAT_MODE


@pytest.fixture
def mock_device():
    """Create a mock device."""
    device = MagicMock()

    # Configure async methods
    device.bind = AsyncMock()
    device.get_all_properties = AsyncMock(
        return_value={
            "pow": 1,  # Power on
            "mode": 4,  # Heat mode
            AwhpProps.HEAT_TEMP_SET.value: 45,
            AwhpProps.COOL_TEMP_SET.value: 22,
            AwhpProps.HOT_WATER_TEMP_SET.value: 50,
            AwhpProps.FAST_HEAT_WATER.value: True,
            AwhpProps.VERSATI_SERIES.value: "III",
        }
    )
    device.push_state_update = AsyncMock()

    # Setup temperature helper methods
    device.t_water_out_pe = MagicMock(return_value=45.5)
    device.t_water_in_pe = MagicMock(return_value=40.0)
    device.hot_water_temp = MagicMock(return_value=50.0)
    device.t_opt_water = MagicMock(return_value=48.0)

    return device


@pytest.fixture
def mock_device_info():
    """Create a mock device info."""
    return MagicMock()


@pytest.fixture
def client_config():
    """Return a client configuration."""
    return {
        "ip": "192.168.1.100",
        "port": 7000,
        "mac": "AA:BB:CC:DD:EE:FF",
        "key": "test_key",
    }


class TestGreeVersatiClientComprehensive:
    """Comprehensive tests for the GreeVersatiClient class."""

    @pytest.mark.asyncio
    async def test_async_get_data_error(
        self, mock_device, mock_device_info, client_config
    ):
        """Test error handling in async_get_data method."""
        # Configure mock device to raise an exception
        mock_device.get_all_properties.side_effect = Exception("Test error")

        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Test that async_get_data raises an exception
            with pytest.raises(Exception, match="Failed to fetch device data"):
                await client.async_get_data()

    @pytest.mark.asyncio
    async def test_initialize_no_params(self, mock_device):
        """Test initialize method when no connection parameters are provided."""
        # Create a client with no connection parameters
        client = GreeVersatiClient()

        # Mock run_discovery to return a device
        client.run_discovery = AsyncMock(return_value=[mock_device])

        # Initialize client
        await client.initialize()

        # Verify run_discovery was called
        client.run_discovery.assert_called_once()

        # Verify device is set
        assert client.device == mock_device

    @pytest.mark.asyncio
    async def test_initialize_no_params_no_devices(self):
        """Test initialize method when no connection parameters are provided and no devices are found."""
        # Create a client with no connection parameters
        client = GreeVersatiClient()

        # Mock run_discovery to return no devices
        client.run_discovery = AsyncMock(return_value=[])

        # Test that initialize raises an exception
        with pytest.raises(Exception, match="No devices discovered"):
            await client.initialize()

    @pytest.mark.asyncio
    async def test_run_discovery(self):
        """Test run_discovery method."""
        # Create mock device
        mock_device = MagicMock()

        # Create mock discovery and listener
        mock_discovery = MagicMock()
        mock_discovery.scan = AsyncMock()
        mock_discovery.add_listener = MagicMock()

        mock_listener = MagicMock()
        mock_listener.get_device.return_value = mock_device

        with (
            patch(
                "custom_components.gree_versati.client.Discovery",
                return_value=mock_discovery,
            ),
            patch(
                "custom_components.gree_versati.client.DiscoveryListener",
                return_value=mock_listener,
            ),
        ):
            # Create a client
            client = GreeVersatiClient()

            # Run discovery
            devices = await client.run_discovery()

            # Verify discovery was called
            mock_discovery.add_listener.assert_called_once_with(mock_listener)
            mock_discovery.scan.assert_called_once()

            # Verify devices were returned
            assert devices == [mock_device]

    @pytest.mark.asyncio
    async def test_run_discovery_no_devices(self):
        """Test run_discovery method when no devices are found."""
        # Create mock discovery and listener
        mock_discovery = MagicMock()
        mock_discovery.scan = AsyncMock()
        mock_discovery.add_listener = MagicMock()

        mock_listener = MagicMock()
        mock_listener.get_device.return_value = None

        with (
            patch(
                "custom_components.gree_versati.client.Discovery",
                return_value=mock_discovery,
            ),
            patch(
                "custom_components.gree_versati.client.DiscoveryListener",
                return_value=mock_listener,
            ),
        ):
            # Create a client
            client = GreeVersatiClient()

            # Run discovery
            devices = await client.run_discovery()

            # Verify discovery was called
            mock_discovery.add_listener.assert_called_once_with(mock_listener)
            mock_discovery.scan.assert_called_once()

            # Verify no devices were returned
            assert devices == []

    @pytest.mark.asyncio
    async def test_property_getters(self, mock_device, mock_device_info, client_config):
        """Test all property getters."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Get data to populate _data
            await client.async_get_data()

            # Test current_temperature
            assert client.current_temperature == 45.5

            # Test target_temperature in heat mode
            client._data["mode"] = HEAT_MODE  # Heat mode
            assert client.target_temperature == 45

            # Test target_temperature in cool mode
            client._data["mode"] = COOL_MODE  # Cool mode
            assert client.target_temperature == 22

            # Test target_temperature in off mode
            client._data["mode"] = None
            assert client.target_temperature is None

            # Test hvac_mode in heat mode
            client._data["mode"] = HEAT_MODE  # Heat mode
            assert client.hvac_mode == "heat"

            # Test hvac_mode in cool mode
            client._data["mode"] = COOL_MODE  # Cool mode
            assert client.hvac_mode == "cool"

            # Test hvac_mode in other mode
            client._data["mode"] = 2  # Other mode
            assert client.hvac_mode == "off"

            # Test is_on
            client._data["power"] = True
            assert client.is_on is True

            client._data["power"] = False
            assert client.is_on is False

            # Test dhw_temperature
            assert client.dhw_temperature == 50.0

            # Test dhw_target_temperature
            assert client.dhw_target_temperature == 50

            # Test dhw_mode
            client._data["fast_heat_water"] = True
            assert client.dhw_mode == "performance"

            client._data["fast_heat_water"] = False
            assert client.dhw_mode == "normal"

    @pytest.mark.asyncio
    async def test_set_temperature_heat(
        self, mock_device, mock_device_info, client_config
    ):
        """Test set_temperature method in heat mode."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Get data to populate _data
            await client.async_get_data()

            # Set temperature in heat mode
            client._data["mode"] = HEAT_MODE  # Heat mode
            await client.set_temperature(50, mode="heat")

            # Verify heat_temp_set was set
            mock_device.set_property.assert_called_with(AwhpProps.HEAT_TEMP_SET, 50)

            # Verify push_state_update was called
            mock_device.push_state_update.assert_called_once()

            # Verify get_all_properties was called (for refresh)
            assert mock_device.get_all_properties.call_count == 2

    @pytest.mark.asyncio
    async def test_set_temperature_cool(
        self, mock_device, mock_device_info, client_config
    ):
        """Test set_temperature method in cool mode."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Get data to populate _data
            await client.async_get_data()

            # Set temperature in cool mode
            client._data["mode"] = COOL_MODE  # Cool mode
            await client.set_temperature(22, mode="cool")

            # Verify cool_temp_set was set
            mock_device.set_property.assert_called_with(AwhpProps.COOL_TEMP_SET, 22)

            # Verify push_state_update was called
            mock_device.push_state_update.assert_called_once()

            # Verify get_all_properties was called (for refresh)
            assert mock_device.get_all_properties.call_count == 2

    @pytest.mark.asyncio
    async def test_set_temperature_auto_mode(
        self, mock_device, mock_device_info, client_config
    ):
        """Test set_temperature method with auto mode detection."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Get data to populate _data
            await client.async_get_data()

            # Set temperature with auto mode detection (heat)
            client._data["mode"] = HEAT_MODE  # Heat mode
            await client.set_temperature(48)

            # Verify heat_temp_set was set
            mock_device.set_property.assert_called_with(AwhpProps.HEAT_TEMP_SET, 48)

            # Reset mock
            mock_device.push_state_update.reset_mock()
            mock_device.set_property.reset_mock()

            # Set temperature with auto mode detection (cool)
            client._data["mode"] = COOL_MODE  # Cool mode
            await client.set_temperature(24)

            # Verify cool_temp_set was set
            mock_device.set_property.assert_called_with(AwhpProps.COOL_TEMP_SET, 24)

    @pytest.mark.asyncio
    async def test_set_dhw_temperature(
        self, mock_device, mock_device_info, client_config
    ):
        """Test set_dhw_temperature method."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Set DHW temperature
            await client.set_dhw_temperature(55)

            # Verify hot_water_temp_set was set
            mock_device.set_property.assert_called_with(
                AwhpProps.HOT_WATER_TEMP_SET, 55
            )

    @pytest.mark.asyncio
    async def test_set_hvac_mode(self, mock_device, mock_device_info, client_config):
        """Test set_hvac_mode method."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Set HVAC mode to heat
            await client.set_hvac_mode("heat")

            # Verify mode was set to HEAT_MODE and power was set to True
            mock_device.set_property.assert_any_call(AwhpProps.MODE, HEAT_MODE)
            mock_device.set_property.assert_any_call(AwhpProps.POWER, value=True)

            # Reset mock
            mock_device.set_property.reset_mock()

            # Set HVAC mode to cool
            await client.set_hvac_mode("cool")

            # Verify mode was set to COOL_MODE and power was set to True
            mock_device.set_property.assert_any_call(AwhpProps.MODE, COOL_MODE)
            mock_device.set_property.assert_any_call(AwhpProps.POWER, value=True)

            # Reset mock
            mock_device.set_property.reset_mock()

            # Set HVAC mode to off
            await client.set_hvac_mode("off")

            # Verify power was set to False
            mock_device.set_property.assert_called_with(AwhpProps.POWER, value=False)

    @pytest.mark.asyncio
    async def test_set_dhw_mode(self, mock_device, mock_device_info, client_config):
        """Test set_dhw_mode method."""
        with (
            patch(
                "custom_components.gree_versati.client.AwhpDevice",
                return_value=mock_device,
            ),
            patch(
                "custom_components.gree_versati.client.DeviceInfo",
                return_value=mock_device_info,
            ),
        ):
            # Create a client
            client = GreeVersatiClient(
                ip=client_config["ip"],
                port=client_config["port"],
                mac=client_config["mac"],
                key=client_config["key"],
            )

            # Initialize client
            await client.initialize()

            # Set DHW mode to performance
            await client.set_dhw_mode("performance")

            # Verify fast_heat_water was set to True
            mock_device.set_property.assert_called_with(
                AwhpProps.FAST_HEAT_WATER, value=True
            )

            # Reset mock
            mock_device.set_property.reset_mock()

            # Set DHW mode to normal
            await client.set_dhw_mode("normal")

            # Verify fast_heat_water was set to False
            mock_device.set_property.assert_called_with(
                AwhpProps.FAST_HEAT_WATER, value=False
            )
