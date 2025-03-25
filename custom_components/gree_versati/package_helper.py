"""Helper module for managing package dependencies."""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Regular expression to match PEP 508 requirement without spaces - manifest.json format
REQUIREMENT_PATTERN = re.compile(r"([^@]+)@(.+)")


def _parse_requirement(req_string: str) -> tuple[str, str]:
    """Parse a requirement string into package name and URL."""
    # Use regex to extract package name and URL
    match = REQUIREMENT_PATTERN.match(req_string)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # For requirements without URL
    return req_string.strip(), ""


def _install_package(package_url: str) -> None:
    """Install a package using pip directly."""
    _LOGGER.info("Installing %s", package_url)
    try:
        # S603: subprocess call with package from trusted source (manifest.json)
        subprocess.check_call(  # noqa: S603
            [sys.executable, "-m", "pip", "install", "--upgrade", package_url],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        _LOGGER.exception("Error installing package %s", package_url)
        raise


def _uninstall_package(package_name: str) -> None:
    """Uninstall a package using pip directly."""
    _LOGGER.info("Uninstalling %s", package_name)
    try:
        # S603: subprocess call with package from trusted source (manifest.json)
        subprocess.check_call(  # noqa: S603
            [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        _LOGGER.exception("Error uninstalling package %s", package_name)
        # Don't raise here, as we still want to try the install


async def _read_manifest_file(file_path: Path) -> dict:
    """Read manifest file asynchronously."""
    import asyncio

    def _read_file() -> dict[str, Any]:
        with file_path.open("r", encoding="utf-8") as manifest_file:
            return json.load(manifest_file)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _read_file)


async def force_update_dependency(hass: HomeAssistant) -> None:
    """Force update/reinstall dependencies from manifest.json."""
    try:
        # Get manifest path relative to this file
        manifest_path = Path(__file__).resolve().parent / "manifest.json"

        # Read manifest file
        manifest = await _read_manifest_file(manifest_path)

        # Get requirements
        requirements = manifest.get("requirements", [])
        if not requirements:
            _LOGGER.warning("No requirements found in manifest.json")
            return

        for req in requirements:
            pkg_name, pkg_url = _parse_requirement(req)

            if not pkg_name:
                _LOGGER.warning("Could not parse requirement: %s", req)
                continue

            # If we have a URL, it's a direct install
            if pkg_url:
                _LOGGER.info("Reinstalling %s from %s", pkg_name, pkg_url)
                try:
                    # Uninstall first to ensure clean install
                    await hass.async_add_executor_job(_uninstall_package, pkg_name)

                    # Now install with the URL
                    await hass.async_add_executor_job(_install_package, pkg_url)
                    _LOGGER.info("Successfully reinstalled %s", pkg_name)
                except (OSError, subprocess.SubprocessError):
                    _LOGGER.exception("Failed to reinstall %s", pkg_name)
            else:
                # Regular package install
                _LOGGER.info("Reinstalling %s", pkg_name)
                try:
                    # Uninstall first
                    await hass.async_add_executor_job(_uninstall_package, pkg_name)

                    # Then install
                    await hass.async_add_executor_job(_install_package, pkg_name)
                    _LOGGER.info("Successfully reinstalled %s", pkg_name)
                except (OSError, subprocess.SubprocessError):
                    _LOGGER.exception("Failed to reinstall %s", pkg_name)

    except (OSError, json.JSONDecodeError):
        _LOGGER.exception("Error handling dependency installation")
