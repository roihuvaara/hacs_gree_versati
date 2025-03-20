#!/bin/bash
set -e

# Run all tests or specific tests if arguments are provided
if [ $# -eq 0 ]; then
  echo "Running all tests..."
  python -m pytest -xvs tests/
else
  echo "Running specific tests: $@"
  python -m pytest -xvs "$@"
fi