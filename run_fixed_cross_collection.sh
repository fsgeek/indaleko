#!/bin/bash
# Run the fixed cross-collection test script

# Set the Python virtual environment
if [ -f .venv-linux-python3.13/bin/activate ]; then
    source .venv-linux-python3.13/bin/activate
elif [ -f .venv-linux-python3.12/bin/activate ]; then
    source .venv-linux-python3.12/bin/activate
elif [ -f .venv-linux-python3.11/bin/activate ]; then
    source .venv-linux-python3.11/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH=`pwd`

# Run the test script
echo "Running fixed cross-collection test script..."
python research/ablation/run_cross_collection_test_fixed.py

# Check if the test succeeded
if [ $? -eq 0 ]; then
    echo "Test completed successfully!"
else
    echo "Test failed with error code $?"
fi
