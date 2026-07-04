#!/usr/bin/env python3
"""Run all tests for the gree_versati integration."""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def run_tests(
    test_path: str | Path | None = None,
    *,  # Force keyword-only arguments for boolean flags
    verbose: bool = False,
    use_pytest: bool = False,
) -> bool:
    """
    Run all tests or specific test module.

    Args:
        test_path: Optional path to specific test file or directory
        verbose: Whether to show verbose output
        use_pytest: Whether to use pytest instead of unittest

    Returns:
        bool: True if all tests passed, False otherwise

    """
    # Add the repository root to the Python path
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root))

    if use_pytest:
        # Use pytest for running tests
        logger.info("Running tests with pytest")
        cmd: list[str] = ["pytest"]

        # Add verbose flag if requested
        if verbose:
            cmd.append("-v")

        # Add test path if specified
        if test_path:
            cmd.append(str(test_path))

        # Run pytest as a subprocess
        # We're not using untrusted input, so this is safe
        result = subprocess.run(cmd, check=False)  # noqa: S603
        return result.returncode == 0

    # Use unittest for running tests
    logger.info("Running tests with unittest")

    import unittest

    # Create a test loader
    loader = unittest.TestLoader()

    # Load tests
    if test_path:
        # Convert to Path object if it's a string
        test_path_obj = Path(test_path)

        # Run a specific test module
        if test_path_obj.is_file():
            logger.info("Running tests from: %s", test_path)

            # Get the directory and filename
            dirname = str(test_path_obj.parent) or "."
            filename = test_path_obj.name

            # Load the test directly by name if it doesn't start with test_
            if not filename.startswith("test_"):
                # Import the module directly
                sys.path.insert(0, dirname)
                module_name = test_path_obj.stem
                __import__(module_name)
                suite = loader.loadTestsFromName(module_name)
            else:
                # Normal pattern discovery
                suite = loader.discover(dirname, pattern=filename)
        else:
            logger.info("Running tests from directory: %s", test_path)
            suite = loader.discover(str(test_path))
    else:
        # Run all tests in the tests directory
        logger.info("Running all tests from the 'tests' directory")
        suite = loader.discover("tests")

    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)

    # Run the tests
    result = runner.run(suite)

    # Return the result
    return result.wasSuccessful()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run tests for gree_versati integration"
    )
    parser.add_argument(
        "test_path", nargs="?", help="Path to specific test file or directory"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--pytest", action="store_true", help="Use pytest instead of unittest"
    )
    args = parser.parse_args()

    success = run_tests(args.test_path, verbose=args.verbose, use_pytest=args.pytest)
    sys.exit(0 if success else 1)
