#!/usr/bin/env bash
# Run the test suite for Indaleko
set -euo pipefail

# Setup environment (installs dependencies via uv)
python3 utils/setup_env.py --force-install --reset-lock-file

# Execute pytest using uv to ensure venv environment, passing any arguments
uv pytest "$@"