#!/usr/bin/env python3
"""
Test the truth data fixes we've implemented.

This script verifies that our truth data modifications have fixed
the unique constraint issue and data sanity checks pass.
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
from research.ablation.data_sanity_checker import DataSanityChecker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_truth_data")

def run_sanity_checks():
    """Run sanity checks on the truth data."""
    logger.info("Running sanity checks on truth data...")
    
    # Initialize the data sanity checker
    checker = DataSanityChecker(fail_fast=False)
    
    # Run individual checks that focus on truth data
    collections_exist = checker.verify_collections_exist()
    logger.info(f"Collections exist check: {'PASS' if collections_exist else 'FAIL'}")
    
    truth_integrity = checker.verify_truth_data_integrity()
    logger.info(f"Truth data integrity check: {'PASS' if truth_integrity else 'FAIL'}")
    
    truth_entities = checker.verify_truth_entities_exist()
    logger.info(f"Truth entities exist check: {'PASS' if truth_entities else 'FAIL'}")
    
    truth_query_ids = checker.verify_truth_query_ids()
    logger.info(f"Truth query IDs check: {'PASS' if truth_query_ids else 'FAIL'}")
    
    query_execution = checker.verify_query_execution()
    logger.info(f"Query execution check: {'PASS' if query_execution else 'FAIL'}")
    
    # Summarize results
    all_passed = all([
        collections_exist,
        truth_integrity,
        truth_entities,
        truth_query_ids,
        query_execution
    ])
    
    if all_passed:
        logger.info("All truth data checks PASSED!")
        return True
    else:
        logger.error("Some truth data checks FAILED")
        return False

def main():
    """Main entry point."""
    logger.info("Testing truth data fixes...")
    
    # Run the sanity checks
    success = run_sanity_checks()
    
    if success:
        logger.info("Truth data tests PASSED")
        return 0
    else:
        logger.error("Truth data tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())