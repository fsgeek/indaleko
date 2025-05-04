#!/usr/bin/env bash
# Run the test suite for Indaleko
set -euo pipefail

# Upgrade pip and install test dependencies
python3 -m pip install --upgrade pip
pip install .[test]

# Execute pytest with any passed arguments
pytest "$@"