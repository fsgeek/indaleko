#!/usr/bin/env python3
"""Test script for the ablation fixes."""

import os
import sys
import logging
import argparse
from pathlib import Path

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description="Test ablation fixes")
parser.add_argument("--count", type=int, default=5, help="Number of test entities to create")
parser.add_argument("--queries", type=int, default=3, help="Number of queries to generate")
args = parser.parse_args()

# Import test components
from research.ablation.collectors.location_collector import LocationActivityCollector
from research.ablation.recorders.location_recorder import LocationActivityRecorder
from research.ablation.ablation_tester import AblationTester
from research.ablation.query.enhanced.enhanced_query_generator import EnhancedQueryGenerator

# Test process
def run_test():
    """Run a focused test of the ablation framework fixes."""
    logger.info("Testing ablation fixes...")
    
    # Initialize tester
    tester = AblationTester()
    
    # Generate location test data
    logger.info("Generating test data...")
    collector = LocationActivityCollector()
    recorder = LocationActivityRecorder()
    
    # Generate synthetic data
    synthetic_data = collector.generate_truth_data(args.count)
    recorder.record_truth_data(synthetic_data, replace_existing=True)
    
    # Generate other collections with empty data for testing
    # These should be treated as valid "no matches expected" cases
    logger.info("Generating empty test collections for cross-collection testing...")
    collections = ["AblationTaskActivity", "AblationMusicActivity"]
    
    # Generate queries
    logger.info("Generating test queries...")
    query_generator = EnhancedQueryGenerator()
    queries = query_generator.generate_queries(args.queries, "location")
    
    # Create truth data
    for query_id, query_text in queries:
        logger.info(f"Processing query: {query_text}")
        
        # Set up unified truth data structure 
        unified_truth = {
            "AblationLocationActivity": [e["_key"] for e in synthetic_data[:3]],
            "AblationTaskActivity": [],  # Empty but valid
            "AblationMusicActivity": []  # Empty but valid
        }
        
        # Store truth data
        logger.info(f"Storing truth data for query {query_id}")
        tester.store_unified_truth_data(query_id, unified_truth)
        
        # Test retrieval for location collection (should have entities)
        loc_truth = tester.get_collection_truth_data(query_id, "AblationLocationActivity")
        logger.info(f"Location truth data retrieved: {loc_truth}")
        
        # Test retrieval for task collection (should be empty but valid)
        task_truth = tester.get_collection_truth_data(query_id, "AblationTaskActivity")
        logger.info(f"Task truth data retrieved: {task_truth}")

if __name__ == "__main__":
    run_test()