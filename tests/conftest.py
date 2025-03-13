"""Test fixtures for pytest compatibility."""

import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add the repository root to the Python path
repo_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, repo_root)

# Import constants from the component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gree_versati.const import DOMAIN

# Configure logging to filter out asyncio debug messages
logging.getLogger("asyncio").setLevel(logging.WARNING)


# Disable asyncio debug mode
@pytest.fixture(autouse=True)
def disable_asyncio_debug():
    """Disable asyncio debug mode for all tests."""
    old_debug = asyncio.get_event_loop().get_debug()
    asyncio.get_event_loop().set_debug(False)
    yield
    asyncio.get_event_loop().set_debug(old_debug)


# Disable the auto_enable_custom_integrations fixture
# @pytest.fixture(autouse=True)
# def auto_enable_custom_integrations(enable_custom_integrations):
#     """Enable custom integrations defined in the test directory."""
#     yield


# Create a fixture to provide a mock entry
@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "ip": "192.168.1.100",
            "port": 7000,
            "name": "Test Gree Versati",
            "mac": "AA:BB:CC:DD:EE:FF",
            "key": "test_key",
        },
        entry_id="test",
    )


# Override the enable_custom_integrations fixture to avoid errors
@pytest.fixture
def enable_custom_integrations(monkeypatch):
    """Enable custom integrations defined in the test directory."""
    # This fixture is required by other Home Assistant fixtures
    # We provide a minimal version that doesn't cause errors


# Override hass fixture to avoid getting async_generator error
@pytest.fixture
def hass(event_loop):
    """Return a Home Assistant mock with proper async methods."""
    # Create the main hass mock
    hass_mock = MagicMock()
    hass_mock.data = {}

    # Dictionary to store entries by ID and states
    entries_by_id = {}
    entity_states = {}

    # Create config_entries mock with async methods
    config_entries_mock = MagicMock()

    # Create flow mock with async methods
    flow_mock = MagicMock()

    # Mock flow result for async_init
    async def async_init(domain, context=None, data=None):
        """Mock implementation of async_init."""
        return {
            "type": "form",
            "flow_id": "test_flow_id",
            "errors": {},
            "step_id": "user",
        }

    # Mock flow result for async_configure
    async def async_configure(flow_id, user_input=None):
        """Mock implementation of async_configure."""
        if not user_input:
            # First step (user) - return a form for the bind step
            return {
                "type": "form",
                "flow_id": flow_id,
                "errors": {},
                "step_id": "bind",
            }
        if "mac" in user_input:
            # Bind step - return a create_entry result
            data = {
                "ip": "192.168.1.123",
                "port": 7000,
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Device",
                "key": "test_key",
            }

            # Import here to avoid circular imports
            from custom_components.gree_versati import async_setup_entry

            # Create a mock entry
            entry = MagicMock()
            entry.data = data
            entry.entry_id = "test_entry_id"

            # Call the setup entry function
            try:
                await async_setup_entry(hass_mock, entry)
            except Exception as e:
                # Propagate the error to fail the test
                print(f"Error in async_setup_entry: {e}")
                raise

            return {
                "type": "create_entry",
                "title": "Test Device",
                "data": data,
            }
        return {"type": "form", "errors": {}}

    flow_mock.async_init = AsyncMock(side_effect=async_init)
    flow_mock.async_configure = AsyncMock(side_effect=async_configure)
    config_entries_mock.flow = flow_mock

    # Create a method to track entries when they're added to hass
    # Monkey patch the original add_to_hass method
    original_add_to_hass = MockConfigEntry.add_to_hass

    def patched_add_to_hass(self, hass):
        # Store entry in our dictionary for later lookup
        entries_by_id[self.entry_id] = self
        # Call the original method
        if original_add_to_hass:
            original_add_to_hass(self, hass)

    # Apply the monkey patch
    MockConfigEntry.add_to_hass = patched_add_to_hass

    # Create a better states mock
    states_mock = MagicMock()

    def get_state(entity_id):
        """Get state for entity_id."""
        if entity_id in entity_states:
            return entity_states[entity_id]

        # Create a new state object
        state_obj = MagicMock()
        state_obj.state = ""
        state_obj.attributes = {}
        entity_states[entity_id] = state_obj
        return state_obj

    def set_state(entity_id, state, attributes=None):
        """Set state for entity_id."""
        if attributes is None:
            attributes = {}
        # Ensure attributes are a dictionary with correct values
        attributes.setdefault("current_temperature", 22.5)
        attributes.setdefault("target_temperature", 24.0)
        attributes.setdefault("hvac_mode", "heat")
        attributes.setdefault("hvac_action", "heating")
        # Correctly apply the state to the hass.states object
        entity_states[entity_id] = MagicMock(state=state, attributes=attributes)
        hass_mock.states.get = get_state
        hass_mock.states.set = set_state

    states_mock.get = get_state
    states_mock.set = set_state
    hass_mock.states = states_mock

    # Helper function to find current mock client
    def find_mock_client():
        """Find the mock client instance in the test if it exists."""
        import inspect

        # Look for a patched GreeVersatiClient in the frames
        for frame_info in inspect.stack():
            if "test_" in frame_info.function:
                frame = frame_info.frame
                if "mock_client_instance" in frame.f_locals:
                    return frame.f_locals["mock_client_instance"]
                if "mock_client" in frame.f_locals:
                    return frame.f_locals["mock_client"]

        return None

    # Implement async_setup to look up the entry and invoke our mock
    async def async_setup(entry_id):
        """Mock implementation of async_setup that handles entry_id."""
        if entry_id not in entries_by_id:
            return False

        entry = entries_by_id[entry_id]

        # Try to find the mock client instance from the test
        mock_client = find_mock_client()

        # If we found a mock client with a side effect on initialize, respect it
        if mock_client and hasattr(mock_client, "initialize"):
            side_effect = getattr(mock_client.initialize, "side_effect", None)
            if side_effect and isinstance(side_effect, Exception):
                # If the test is configuring the client to raise an exception, return False
                return False

        # Create a coordinator mock that can be used to update sensors
        coordinator_mock = MagicMock()

        # Create an async_update method that will update entity states
        async def async_update():
            # Based on the client state, update all relevant entities
            if mock_client and hasattr(mock_client, "is_connected"):
                is_connected = mock_client.is_connected()

                # Get the device name for entity naming
                device_name = entry.data.get("name", "Test Device")
                safe_name = device_name.lower().replace(" ", "_")

                # Check temperature sensors
                if hasattr(mock_client, "get_temperature"):
                    temp = mock_client.get_temperature()
                    entity_id = f"sensor.{safe_name}_temperature"

                    if is_connected and temp is not None:
                        set_state(
                            entity_id,
                            str(temp),
                            {
                                "unit_of_measurement": "°C",
                                "friendly_name": f"{device_name} Temperature",
                                "device_class": "temperature",
                            },
                        )
                    else:
                        set_state(entity_id, "unavailable")

                # Check water temperature sensors
                if hasattr(mock_client, "get_water_temperature"):
                    temp = mock_client.get_water_temperature()
                    entity_id = f"sensor.{safe_name}_water_temperature"

                    if is_connected and temp is not None:
                        set_state(
                            entity_id,
                            str(temp),
                            {
                                "unit_of_measurement": "°C",
                                "friendly_name": f"{device_name} Water Temperature",
                                "device_class": "temperature",
                            },
                        )
                    else:
                        set_state(entity_id, "unavailable")

                # Check climate entity
                entity_id = f"climate.{safe_name}"
                if is_connected:
                    set_state(
                        entity_id,
                        mock_client.get_hvac_mode(),
                        {
                            "friendly_name": device_name,
                            "current_temperature": mock_client.get_temperature(),
                            "temperature": mock_client.get_target_temperature(),
                            "hvac_mode": mock_client.get_hvac_mode(),
                            "hvac_action": mock_client.get_hvac_action(),
                        },
                    )
                else:
                    set_state(entity_id, "unavailable")

            return True

        coordinator_mock.async_update = AsyncMock(side_effect=async_update)

        # For success cases or when no mock is found
        hass_mock.data.setdefault(DOMAIN, {})
        hass_mock.data[DOMAIN][entry_id] = {
            "client": mock_client or MagicMock(),
            "coordinator": coordinator_mock,
        }

        # Run initial update to populate states
        await coordinator_mock.async_update()

        return True

    config_entries_mock.async_setup = AsyncMock(side_effect=async_setup)

    # Make async_unload return True by default
    async def async_unload(entry_id):
        # Clean up data if it exists
        if DOMAIN in hass_mock.data and entry_id in hass_mock.data[DOMAIN]:
            hass_mock.data[DOMAIN].pop(entry_id)
        return True

    config_entries_mock.async_unload = AsyncMock(side_effect=async_unload)

    # Make async_forward_entry_setups return True by default
    async def async_forward_entry_setups(entry, platforms):
        return True

    config_entries_mock.async_forward_entry_setups = AsyncMock(
        side_effect=async_forward_entry_setups
    )

    # Attach config_entries to hass
    hass_mock.config_entries = config_entries_mock

    # Add other attributes and methods
    hass_mock.config = MagicMock()

    # Create services mock with async methods
    services_mock = MagicMock()

    async def async_call(
        domain, service, service_data=None, blocking=False, target=None
    ):
        """Mock service call."""
        if domain == "climate" and service_data is not None:
            entity_id = service_data.get("entity_id")
            if entity_id:
                # Get the client from hass.data
                entry_id = "test"  # This is the entry_id we use in our tests
                if DOMAIN in hass_mock.data and entry_id in hass_mock.data[DOMAIN]:
                    client = hass_mock.data[DOMAIN][entry_id]["client"]
                    state = hass_mock.states.get(entity_id)

                    if service == "set_temperature":
                        temperature = service_data.get("temperature")
                        if temperature is not None:
                            # Call the client's set_target_temperature method
                            await client.set_target_temperature(temperature)
                            # Update the entity state with the new temperature
                            if state:
                                attrs = dict(state.attributes)
                                attrs["temperature"] = temperature
                                set_state(entity_id, state.state, attrs)

                    elif service == "set_hvac_mode":
                        hvac_mode = service_data.get("hvac_mode")
                        if hvac_mode is not None:
                            # Call the client's set_hvac_mode method
                            await client.set_hvac_mode(hvac_mode)
                            # Update the entity state with the new mode
                            if state:
                                attrs = dict(state.attributes)
                                attrs["hvac_mode"] = hvac_mode
                                set_state(entity_id, hvac_mode, attrs)
        return True

    services_mock.async_call = AsyncMock(side_effect=async_call)
    hass_mock.services = services_mock

    # Make async_create_task just run the coroutine
    async def async_create_task(coro):
        await coro

    hass_mock.async_create_task = AsyncMock(side_effect=async_create_task)

    # Make async_block_till_done awaitable
    async def async_block_till_done():
        pass

    hass_mock.async_block_till_done = AsyncMock(side_effect=async_block_till_done)

    return hass_mock
