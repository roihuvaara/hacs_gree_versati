#!/bin/bash
# Run pytest with the correct environment setup

# Add the current directory to PYTHONPATH
export PYTHONPATH=.:$PYTHONPATH

# Run pytest with the provided arguments
pytest "$@"