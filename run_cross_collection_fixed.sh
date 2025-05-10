#!/bin/bash
# Run the fixed cross-collection ablation test

# Change to the directory containing the script
cd "$(dirname "$0")" || exit 1

# Ensure virtual environment is activated
if [ -d .venv-linux-python3.13 ]; then
    source .venv-linux-python3.13/bin/activate
elif [ -d .venv-macos-python3.12 ]; then
    source .venv-macos-python3.12/bin/activate
elif [ -d .venv-win32-python3.12/Scripts ]; then
    source .venv-win32-python3.12/Scripts/activate
fi

# Run the focused cross-collection test with fixed implementation
python -m research.ablation.run_cross_collection_test_fixed "$@"