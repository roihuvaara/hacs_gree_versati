#!/usr/bin/env python3
"""Run all tests for the gree_versati integration."""

import os
import sys
import unittest
import argparse


def run_tests(test_path=None, verbose=False):
    """Run all tests or specific test module."""
    # Add the repository root to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Create a test loader
    loader = unittest.TestLoader()

    # Load tests
    if test_path:
        # Run a specific test module
        if os.path.isfile(test_path):
            print(f"Running tests from: {test_path}")

            # Get the directory and filename
            dirname = os.path.dirname(test_path) or "."
            filename = os.path.basename(test_path)

            # Load the test directly by name if it doesn't start with test_
            if not filename.startswith("test_"):
                # Import the module directly
                sys.path.insert(0, dirname)
                module_name = os.path.splitext(filename)[0]
                __import__(module_name)
                suite = loader.loadTestsFromName(module_name)
            else:
                # Normal pattern discovery
                suite = loader.discover(dirname, pattern=filename)
        else:
            print(f"Running tests from directory: {test_path}")
            suite = loader.discover(test_path)
    else:
        # Run all tests in the tests directory
        print("Running all tests from the 'tests' directory")
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
    args = parser.parse_args()

    success = run_tests(args.test_path, args.verbose)
    sys.exit(0 if success else 1)
