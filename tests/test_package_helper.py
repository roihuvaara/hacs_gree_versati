"""Tests for the package_helper module."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.gree_versati.package_helper import (
    _install_package,
    _parse_requirement,
    _read_manifest_file,
    _uninstall_package,
    force_update_dependency,
)


def test_parse_requirement():
    """Test parsing various requirement formats."""
    # Standard format without spaces
    assert _parse_requirement("package@git+url") == ("package", "git+url")

    # With extra whitespace in package name
    assert _parse_requirement("  package@git+url") == ("package", "git+url")

    # With whitespace in URL
    assert _parse_requirement("package@git+url  ") == ("package", "git+url")

    # Plain package without URL
    assert _parse_requirement("simple_package") == ("simple_package", "")

    # Empty string
    assert _parse_requirement("") == ("", "")

    # Package with version and URL
    assert _parse_requirement("package==1.0.5@git+url") == ("package==1.0.5", "git+url")


@patch("subprocess.check_call")
def test_install_package(mock_check_call):
    """Test package installation."""
    # Test successful installation
    _install_package("test-package")
    mock_check_call.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "--upgrade", "test-package"],
        stderr=subprocess.STDOUT,
    )

    # Test exception handling
    mock_check_call.reset_mock()
    mock_check_call.side_effect = subprocess.CalledProcessError(1, "cmd")

    with pytest.raises(subprocess.CalledProcessError):
        _install_package("test-package")

    mock_check_call.assert_called_once()


@patch("subprocess.check_call")
def test_uninstall_package(mock_check_call):
    """Test package uninstallation."""
    # Test successful uninstallation
    _uninstall_package("test-package")
    mock_check_call.assert_called_once_with(
        [sys.executable, "-m", "pip", "uninstall", "-y", "test-package"],
        stderr=subprocess.STDOUT,
    )

    # Test exception handling - should not raise
    mock_check_call.reset_mock()
    mock_check_call.side_effect = subprocess.CalledProcessError(1, "cmd")

    # Should not raise an exception
    _uninstall_package("test-package")

    mock_check_call.assert_called_once()


@pytest.mark.asyncio
async def test_read_manifest_file():
    """Test reading manifest file asynchronously."""
    test_path = Path("test_manifest.json")
    test_content = {"requirements": ["package@git+url"]}

    # Mock file opening and reading
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_open.return_value = mock_file

    with (
        patch("pathlib.Path.open", mock_open),
        patch("json.load", return_value=test_content),
    ):
        result = await _read_manifest_file(test_path)

    assert result == test_content
    mock_open.assert_called_once_with("r", encoding="utf-8")


@pytest.mark.asyncio
async def test_read_manifest_file_exception():
    """Test exception handling in read_manifest_file."""
    test_path = Path("test_manifest.json")

    # Mock the asyncio.get_running_loop function
    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Mock the run_in_executor method
        mock_loop.run_in_executor = AsyncMock()
        mock_loop.run_in_executor.side_effect = FileNotFoundError("File not found")

        # Test the function
        with pytest.raises(FileNotFoundError):
            await _read_manifest_file(test_path)


@pytest.mark.asyncio
@patch("custom_components.gree_versati.package_helper._uninstall_package")
@patch("custom_components.gree_versati.package_helper._install_package")
@patch("custom_components.gree_versati.package_helper._read_manifest_file")
@patch("pathlib.Path.resolve")
async def test_force_update_dependency(
    mock_resolve, mock_read_manifest, mock_install, mock_uninstall
):
    """Test the full dependency update process."""
    # Setup mocks
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock()
    hass.async_add_executor_job.side_effect = lambda func, *args: func(*args)

    # Mock path resolution
    mock_path = MagicMock()
    mock_path.parent = MagicMock()
    mock_path.parent.__truediv__ = MagicMock(return_value="manifest_path")
    mock_resolve.return_value = mock_path

    # Test with valid requirement
    manifest_content = {
        "requirements": [
            "gree_versati@git+https://github.com/roihuvaara/greeclimate@r1.0.5"
        ]
    }
    mock_read_manifest.return_value = manifest_content

    await force_update_dependency(hass)

    # Verify calls
    mock_uninstall.assert_called_once_with("gree_versati")
    mock_install.assert_called_once_with(
        "git+https://github.com/roihuvaara/greeclimate@r1.0.5"
    )

    # Test with missing requirements
    mock_read_manifest.return_value = {}
    mock_uninstall.reset_mock()
    mock_install.reset_mock()

    await force_update_dependency(hass)

    # Verify no calls made when requirements are missing
    mock_uninstall.assert_not_called()
    mock_install.assert_not_called()

    # Test with requirement but no URL
    manifest_content = {"requirements": ["plain_package"]}
    mock_read_manifest.return_value = manifest_content

    await force_update_dependency(hass)

    # Verify calls - uninstall followed by install with same package name
    assert mock_uninstall.call_count == 1
    assert mock_install.call_count == 1
    mock_uninstall.assert_called_with("plain_package")
    mock_install.assert_called_with("plain_package")


@pytest.mark.asyncio
@patch("custom_components.gree_versati.package_helper._read_manifest_file")
async def test_force_update_dependency_exceptions(mock_read_manifest):
    """Test exception handling in force_update_dependency."""
    # Setup mocks
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock()

    # Test file not found
    mock_read_manifest.side_effect = FileNotFoundError("File not found")

    # Should handle exception gracefully
    await force_update_dependency(hass)

    # Test JSON decode error
    mock_read_manifest.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

    # Should handle exception gracefully
    await force_update_dependency(hass)

    # Test with installation error
    mock_read_manifest.return_value = {"requirements": ["test@url"]}
    hass.async_add_executor_job.side_effect = OSError("Installation failed")

    # Should handle exception gracefully
    await force_update_dependency(hass)


@pytest.mark.asyncio
@patch("custom_components.gree_versati.package_helper._read_manifest_file")
async def test_force_update_dependency_subprocess_errors(mock_read_manifest):
    """Test subprocess error handling in force_update_dependency."""
    # Setup mocks
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock()

    # Mock requirements
    mock_read_manifest.return_value = {
        "requirements": ["pkg1@url1", "pkg2@url2", "pkg3"]
    }

    # Test subprocess error during uninstall - for URL requirement
    with patch.object(hass, "async_add_executor_job") as mock_exec:
        # First uninstall fails with subprocess error
        mock_exec.side_effect = [
            subprocess.SubprocessError(
                "Uninstall failed"
            ),  # First call fails (uninstall)
            None,  # Second call succeeds (install)
            None,  # Subsequent calls succeed
            None,
            None,
            None,
        ]

        await force_update_dependency(hass)

        # Verify at least 2 calls were made (tried to continue after error)
        assert mock_exec.call_count >= 2

    # Test subprocess error during install - for URL requirement
    with patch.object(hass, "async_add_executor_job") as mock_exec:
        # First install fails with subprocess error
        mock_exec.side_effect = [
            None,  # First call succeeds (uninstall)
            subprocess.SubprocessError("Install failed"),  # Second call fails (install)
            None,  # Subsequent calls succeed
            None,
            None,
            None,
        ]

        await force_update_dependency(hass)

        # Verify at least 3 calls were made (tried to continue after error)
        assert mock_exec.call_count >= 3

    # Test subprocess error for non-URL requirement
    with patch.object(hass, "async_add_executor_job") as mock_exec:
        # Regular package install fails
        mock_exec.side_effect = [
            None,  # First two calls succeed
            None,
            None,
            None,
            subprocess.SubprocessError(
                "Install failed"
            ),  # Regular package install fails
            None,
        ]

        await force_update_dependency(hass)

        # Verify we tried to process all requirements
        assert mock_exec.call_count >= 5


@pytest.mark.asyncio
async def test_read_manifest_file_complete():
    """Test _read_manifest_file with complete mocking of the event loop."""
    test_path = Path("test_manifest.json")
    test_content = {"data": "content"}

    # Create a mock event loop
    mock_loop = MagicMock()
    mock_loop.run_in_executor = AsyncMock(return_value=test_content)

    # Mock get_running_loop to return our mock loop
    with patch("asyncio.get_running_loop", return_value=mock_loop):
        result = await _read_manifest_file(test_path)

    assert result == test_content
    mock_loop.run_in_executor.assert_called_once()


@pytest.mark.asyncio
async def test_read_manifest_file_with_direct_mocking():
    """Test _read_manifest_file with direct mocking of the inner function."""
    test_path = Path("test_manifest.json")
    test_content = {"test": "data"}

    # Mock file opening and reading
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_open.return_value = mock_file

    # Create a mock for the inner _read_file function
    async def mock_read_file():
        return test_content

    # Mock the run_in_executor to use our mock_read_file
    mock_loop = MagicMock()
    mock_loop.run_in_executor = AsyncMock(return_value=test_content)

    with patch("asyncio.get_running_loop", return_value=mock_loop):
        result = await _read_manifest_file(test_path)

    assert result == test_content
    mock_loop.run_in_executor.assert_called_once()


@pytest.mark.asyncio
async def test_read_manifest_file_run_in_executor():
    """Test the run_in_executor line in _read_manifest_file."""
    test_path = Path("test_manifest.json")
    test_content = {"data": "content"}

    # Create a simple AsyncMock that returns the test_content
    mock_run_in_executor = AsyncMock(return_value=test_content)

    # Create a mock loop with our mocked run_in_executor method
    mock_loop = MagicMock()
    mock_loop.run_in_executor = mock_run_in_executor

    # Patch asyncio.get_running_loop to return our mock loop
    with patch("asyncio.get_running_loop", return_value=mock_loop):
        # Call the function to test
        result = await _read_manifest_file(test_path)

        # Assert that run_in_executor was called
        mock_run_in_executor.assert_called_once()

        # Assert we got our test content back
        assert result == test_content
