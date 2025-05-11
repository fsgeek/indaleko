#!/usr/bin/env python3
"""Simple test for verifying AblationTester changes."""

import logging
import os
import sys
import uuid
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

# Directly import the tester
from research.ablation.ablation_tester import AblationTester

def main():
    """Test the fixed AblationTester."""
    # Create a tester instance
    tester = AblationTester()
    
    # Use a specific UUID that we know exists
    test_uuid = "b735aff6-1e77-505c-a5c2-37d742e023ce"
    test_collection = "AblationLocationActivity"
    
    # Get the truth data directly
    truth_data = tester.get_collection_truth_data(test_uuid, test_collection)
    
    # Log the result
    logger.info(f"Truth data for {test_collection}: {truth_data}")
    logger.info(f"Truth data type: {type(truth_data)}")
    logger.info(f"Truth data is empty: {len(truth_data) == 0}")
    logger.info(f"Truth data is None: {truth_data is None}")
    
    # Try a different collection that should have data
    test_collection2 = "AblationMusicActivity"
    truth_data2 = tester.get_collection_truth_data(test_uuid, test_collection2)
    
    # Log the comparison
    logger.info(f"Truth data for {test_collection2}: {truth_data2}")
    logger.info(f"Truth data type: {type(truth_data2)}")
    logger.info(f"Truth data is empty: {len(truth_data2) == 0}")
    logger.info(f"Truth data count: {len(truth_data2)}")

if __name__ == "__main__":
    main()