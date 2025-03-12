"""Test pytest compatibility."""

import pytest


def test_module_import():
    """Test that the greeclimate_versati_fork module can be imported."""
    import greeclimate_versati_fork

    assert greeclimate_versati_fork is not None
    print(
        f"Found greeclimate_versati_fork module at: {greeclimate_versati_fork.__file__}"
    )


@pytest.mark.asyncio
async def test_async_function():
    """Test that async functions work with pytest."""
    # This is a simple async function that should work
    result = await async_example()
    assert result == "success"


async def async_example():
    """Example async function to test asyncio support."""
    return "success"


def test_with_hass_fixture(hass):
    """Test that the mocked hass fixture works."""
    # The hass fixture should be a MagicMock with data attribute
    assert hasattr(hass, "data")
    assert isinstance(hass.data, dict)


def test_with_config_entry(mock_config_entry):
    """Test that the mock_config_entry fixture works."""
    assert mock_config_entry.domain == "gree_versati"
    assert mock_config_entry.data["ip"] == "192.168.1.100"
    assert mock_config_entry.data["port"] == 7000
