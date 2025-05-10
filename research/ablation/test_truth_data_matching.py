#!/usr/bin/env python3
"""
Controlled test for truth data matching in ablation framework.

This script performs a targeted test of the fixed query execution and truth data matching
without running the full ablation test suite.
"""

import logging
import sys
import time
import uuid
from typing import Dict, Any, List, Set

from db.db_config import IndalekoDBConfig
from .ablation_tester import AblationTester


def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger(__name__)


def run_controlled_test(collection_name: str, query_id: str = None, create_truth: bool = False):
    """
    Run a controlled test on a specific collection.
    
    Args:
        collection_name: Name of the collection to test
        query_id: Optional query ID to use (will generate one if not provided)
        create_truth: Whether to create truth data if it doesn't exist
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running controlled test on collection {collection_name}")
    
    # Create an AblationTester instance
    tester = AblationTester()
    
    # Generate a query ID if not provided
    if not query_id:
        query_id = str(uuid.uuid4())
    
    logger.info(f"Using query ID: {query_id}")
    
    # Check if the collection exists
    if not tester.db.has_collection(collection_name):
        logger.error(f"Collection {collection_name} does not exist")
        return False
    
    # Get the current truth data for this collection/query
    truth_data = tester.get_truth_data(query_id, collection_name)
    
    # If we have no truth data and create_truth is True, create some truth data
    if not truth_data and create_truth:
        logger.info(f"No truth data found for {query_id} in {collection_name}, creating some...")
        
        # Get 5 deterministic entities from the collection
        aql_query = f"""
        FOR doc IN {collection_name}
        SORT doc._key
        LIMIT 5
        RETURN doc._key
        """
        
        cursor = tester.db.aql.execute(aql_query)
        entity_keys = [doc for doc in cursor]
        
        if not entity_keys:
            logger.error(f"No entities found in collection {collection_name}")
            return False
        
        logger.info(f"Selected {len(entity_keys)} entities for truth data: {entity_keys}")
        
        # Store the truth data
        tester.store_truth_data(query_id, collection_name, entity_keys)
        
        # Re-fetch the truth data to confirm it was stored
        truth_data = tester.get_truth_data(query_id, collection_name)
        
        if not truth_data:
            logger.error(f"Failed to store truth data for {query_id} in {collection_name}")
            return False
    
    # If we still have no truth data, we can't proceed
    if not truth_data:
        logger.error(f"No truth data available for {query_id} in {collection_name}")
        return False
    
    logger.info(f"Found {len(truth_data)} truth data entries for {query_id} in {collection_name}")
    logger.info(f"Truth data: {truth_data}")
    
    # Create a test query
    if "MusicActivity" in collection_name:
        query_text = "Find all songs by Taylor Swift"
    elif "LocationActivity" in collection_name:
        query_text = "Find all locations in New York"
    elif "TaskActivity" in collection_name:
        query_text = "Find all document tasks"
    elif "CollaborationActivity" in collection_name:
        query_text = "Find all meetings"
    elif "StorageActivity" in collection_name:
        query_text = "Find all document files"
    elif "MediaActivity" in collection_name:
        query_text = "Find all video content"
    else:
        query_text = f"Find data in {collection_name}"
    
    logger.info(f"Using test query: '{query_text}'")
    
    # Execute the query
    results, execution_time, aql_query = tester.execute_query(query_id, query_text, collection_name)
    
    logger.info(f"Query execution completed in {execution_time}ms")
    logger.info(f"Query returned {len(results)} results")
    logger.info(f"AQL query: {aql_query}")
    
    # Calculate metrics
    metrics = tester.calculate_metrics(query_id, results, collection_name)
    
    logger.info(f"Metrics: precision={metrics.precision:.4f}, recall={metrics.recall:.4f}, f1_score={metrics.f1_score:.4f}")
    logger.info(f"True positives: {metrics.true_positives}, False positives: {metrics.false_positives}, False negatives: {metrics.false_negatives}")
    
    # Verify that truth data is being properly matched
    expected_match_count = len(truth_data)
    actual_match_count = metrics.true_positives
    
    if actual_match_count < expected_match_count:
        logger.error(f"FAILED: Not all truth data matched! Expected {expected_match_count}, got {actual_match_count}")
        # Identify which truth entities are missing
        result_keys = set(doc.get("_key") for doc in results)
        missing_keys = truth_data - result_keys
        logger.error(f"Missing keys: {missing_keys}")
        return False
    
    logger.info(f"SUCCESS: All {expected_match_count} truth entities matched correctly!")
    return True


def test_ablated_collection(collection_name: str, query_id: str = None):
    """
    Test how an ablated collection is handled.
    
    Args:
        collection_name: Name of the collection to test
        query_id: Optional query ID to use (will generate one if not provided)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Testing ablated collection behavior for {collection_name}")
    
    # Create an AblationTester instance
    tester = AblationTester()
    
    # Generate a query ID if not provided
    if not query_id:
        query_id = str(uuid.uuid4())
    
    # Get or create truth data
    truth_data = tester.get_truth_data(query_id, collection_name)
    if not truth_data:
        # We need to create some truth data first
        run_controlled_test(collection_name, query_id, create_truth=True)
        truth_data = tester.get_truth_data(query_id, collection_name)
    
    # Ablate the collection
    logger.info(f"Ablating collection {collection_name}...")
    ablation_success = tester.ablate_collection(collection_name)
    
    if not ablation_success:
        logger.error(f"Failed to ablate collection {collection_name}")
        return False
    
    # Create a test query
    query_text = f"Find data in {collection_name}"
    
    try:
        # Execute the query on the ablated collection
        logger.info(f"Executing query on ablated collection {collection_name}...")
        results, execution_time, aql_query = tester.execute_query(query_id, query_text, collection_name)
        
        logger.info(f"Query execution completed in {execution_time}ms")
        logger.info(f"Query returned {len(results)} results (should be 0 for ablated collection)")
        
        # Calculate metrics
        logger.info("Calculating metrics for ablated collection...")
        metrics = tester.calculate_metrics(query_id, results, collection_name)
        
        logger.info(f"Metrics: precision={metrics.precision:.4f}, recall={metrics.recall:.4f}, f1_score={metrics.f1_score:.4f}")
        logger.info(f"True positives: {metrics.true_positives}, False positives: {metrics.false_positives}, False negatives: {metrics.false_negatives}")
        
        # Verify expected behavior for ablated collection
        # - We expect 0 results
        # - We expect 0 true positives
        # - We expect 0 false positives
        # - We expect false_negatives = len(truth_data)
        # - We expect precision = undefined (0 in practice)
        # - We expect recall = 0
        # - We expect f1_score = 0
        
        test_passed = True
        
        if len(results) > 0:
            logger.error(f"FAILED: Got {len(results)} results for ablated collection, expected 0")
            test_passed = False
        
        if metrics.true_positives > 0:
            logger.error(f"FAILED: Got {metrics.true_positives} true positives for ablated collection, expected 0")
            test_passed = False
        
        if metrics.false_positives > 0:
            logger.error(f"FAILED: Got {metrics.false_positives} false positives for ablated collection, expected 0")
            test_passed = False
        
        if metrics.false_negatives != len(truth_data):
            logger.error(f"FAILED: Got {metrics.false_negatives} false negatives for ablated collection, expected {len(truth_data)}")
            test_passed = False
        
        if metrics.precision > 0:
            logger.error(f"FAILED: Got precision {metrics.precision} for ablated collection, expected 0")
            test_passed = False
        
        if metrics.recall > 0:
            logger.error(f"FAILED: Got recall {metrics.recall} for ablated collection, expected 0")
            test_passed = False
        
        if metrics.f1_score > 0:
            logger.error(f"FAILED: Got F1 score {metrics.f1_score} for ablated collection, expected 0")
            test_passed = False
        
        if test_passed:
            logger.info("SUCCESS: Ablated collection test passed! Behavior is as expected.")
        
    finally:
        # Always restore the collection
        logger.info(f"Restoring collection {collection_name}...")
        restore_success = tester.restore_collection(collection_name)
        
        if not restore_success:
            logger.error(f"Failed to restore collection {collection_name}")
            return False
    
    return test_passed


def main():
    """Main entry point for the test script."""
    logger = setup_logging()
    logger.info("Starting controlled test for truth data matching")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test truth data matching in ablation framework")
    parser.add_argument("--collection", type=str, help="Collection to test")
    parser.add_argument("--query-id", type=str, help="Query ID to use")
    parser.add_argument("--create-truth", action="store_true", help="Create truth data if it doesn't exist")
    parser.add_argument("--test-ablation", action="store_true", help="Test ablated collection behavior")
    parser.add_argument("--all-collections", action="store_true", help="Test all ablation collections")
    args = parser.parse_args()
    
    # Check for required arguments
    if not args.collection and not args.all_collections:
        logger.error("Either --collection or --all-collections is required")
        return 1
    
    # If testing all collections, discover available collections
    if args.all_collections:
        try:
            db_config = IndalekoDBConfig()
            db = db_config.get_arangodb()
            collections = []

            # ArangoDB collections() returns a list of collection objects or dicts, not just names
            for collection in db.collections():
                # Get the collection name (handle both object and dict cases)
                if hasattr(collection, 'name'):
                    collection_name = collection.name
                elif isinstance(collection, dict) and 'name' in collection:
                    collection_name = collection['name']
                else:
                    continue

                if collection_name.startswith("Ablation") and "Activity" in collection_name:
                    collections.append(collection_name)

            if not collections:
                logger.error("No ablation collections found")
                return 1

            logger.info(f"Found {len(collections)} ablation collections: {collections}")
        except Exception as e:
            logger.error(f"Failed to discover ablation collections: {e}")
            return 1
    else:
        collections = [args.collection]
    
    # Run tests for each collection
    all_passed = True
    
    for collection_name in collections:
        logger.info(f"=== Testing collection {collection_name} ===")
        
        if args.test_ablation:
            test_passed = test_ablated_collection(collection_name, args.query_id)
        else:
            test_passed = run_controlled_test(collection_name, args.query_id, args.create_truth)
        
        if not test_passed:
            all_passed = False
            logger.error(f"Test for collection {collection_name} failed!")
        else:
            logger.info(f"Test for collection {collection_name} passed!")
    
    if all_passed:
        logger.info("✅ All tests passed! The fixes appear to be working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Issues remain with the ablation framework.")
        return 1


if __name__ == "__main__":
    sys.exit(main())