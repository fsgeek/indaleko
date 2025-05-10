#!/usr/bin/env python3
"""
Clear all truth data from AblationQueryTruth collection.

This script is designed to remove any test or synthetic truth data
that might interfere with comprehensive ablation experiments.
"""

import os
import sys
import logging
from pathlib import Path

# Set up path
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = current_path.parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from db.db_config import IndalekoDBConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clear_truth_data")

def main():
    """Clear all data from the AblationQueryTruth collection."""
    logger.info("Connecting to database...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    # Target collection
    truth_collection = "AblationQueryTruth"
    
    # Check if collection exists
    if not db.has_collection(truth_collection):
        logger.info(f"Collection {truth_collection} does not exist. Nothing to clear.")
        return 0
    
    # Clear all data from the collection
    logger.info(f"Clearing all data from {truth_collection}...")
    try:
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        count = db.collection(truth_collection).count()
        logger.info(f"Successfully cleared collection {truth_collection}. Contains {count} documents after clearing.")
        return 0
    except Exception as e:
        logger.error(f"CRITICAL: Failed to clear collection {truth_collection}: {e}")
        sys.exit(1)  # Fail-stop on error

if __name__ == "__main__":
    sys.exit(main())