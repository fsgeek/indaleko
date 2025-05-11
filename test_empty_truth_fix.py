#!/usr/bin/env python3
"""Test script for empty truth data fixes in the ablation framework."""

import logging
import os
import sys
import uuid
from typing import Any, Dict, List

from research.ablation.ablation_tester import AblationTester, AblationConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_empty_truth_fix")

def main():
    """Main function to test the empty truth data fixes."""
    logger.info("Starting empty truth data fix test")

    # Initialize the ablation tester
    tester = AblationTester()

    # Step 1: Create a query ID to use for this test
    query_id = uuid.uuid4()
    logger.info(f"Using query ID: {query_id}")

    # Step 2: Create truth data with both populated and empty collections
    collections_to_test = [
        "AblationMusicActivity",
        "AblationLocationActivity",
        "AblationTaskActivity",
        "AblationCollaborationActivity",
        "AblationStorageActivity"
    ]

    # Set up truth data with synthetic entities (bypass entity verification)
    # We use synthetic prefixes so they don't need to exist in the database
    truth_data = {
        # Populated data
        "AblationMusicActivity": ["synthetic_music_doc_1", "synthetic_music_doc_2", "synthetic_music_doc_3"],
        # Empty but valid data
        "AblationLocationActivity": [],
        # Populated data
        "AblationTaskActivity": ["synthetic_task_doc_1", "synthetic_task_doc_2"],
        # Empty but valid data
        "AblationCollaborationActivity": [],
        # Populated data
        "AblationStorageActivity": ["synthetic_storage_doc_1"]
    }

    # Set environment variable to skip entity validation (since our test entities don't exist)
    os.environ["ABLATION_SKIP_ENTITY_VALIDATION"] = "1"

    try:
        # Step 3: Store the truth data
        logger.info("Storing unified truth data with empty collection lists")
        tester.store_unified_truth_data(query_id, truth_data)
        logger.info("Successfully stored unified truth data")

        # Step 4: Verify the truth data was stored correctly
        unified_truth = tester.get_unified_truth_data(query_id)
        if not unified_truth:
            logger.error("Failed to retrieve unified truth data")
            return False

        # Check that all our collections are stored and empty/non-empty status is preserved
        for collection, entities in truth_data.items():
            if collection not in unified_truth:
                logger.error(f"Collection {collection} missing from unified truth data")
                return False

            # Check empty/populated status
            expected_empty = len(entities) == 0
            actual_empty = len(unified_truth[collection]) == 0

            logger.info(f"Collection {collection}: Expected empty: {expected_empty}, Got empty: {actual_empty}")
            if expected_empty != actual_empty:
                logger.error(f"Empty status mismatch for {collection}")
                return False

        # Step 5: Test collection-specific truth data retrieval
        for collection in collections_to_test:
            collection_truth = tester.get_collection_truth_data(query_id, collection)
            is_empty = len(collection_truth) == 0
            expected_empty = len(truth_data.get(collection, [])) == 0
            logger.info(f"Retrieved truth data for {collection}: Empty: {is_empty}")

            if is_empty != expected_empty:
                logger.error(f"Empty status mismatch for collection {collection}")
                return False

        # Step 6: Test query construction with empty collections
        # We'll just check a couple of key collections that should behave differently

        # Test a collection with empty truth data
        empty_collection = "AblationLocationActivity"
        search_terms = {"location_name": "Home"}
        logger.info(f"Testing query construction for empty collection: {empty_collection}")

        empty_truth = tester.get_collection_truth_data(query_id, empty_collection)
        aql_query, bind_vars = tester._build_combined_query(empty_collection, search_terms, empty_truth)

        # Verify the special empty truth handling is working
        if "truth_keys" not in bind_vars:
            logger.error("Missing truth_keys in bind variables for empty collection")
            return False

        if bind_vars["truth_keys"] != ["__EMPTY_TRUTH_SET_NO_MATCHES_EXPECTED__"]:
            logger.error("Missing special key for empty truth set")
            return False

        logger.info("Empty collection query construction test passed!")

        # Step 7: Let's try both scenarios for metrics calculation with empty truth data

        # Test Case 1: Ablated collection with empty truth data (should be 1.0/1.0/1.0)
        empty_results = []
        empty_truth_data = set()
        collection_name = "TestEmptyCollection"

        # Create a test AblationResult with an empty truth data set for an ablated collection
        logger.info("Testing metrics calculation with empty truth data for ablated collection...")
        metrics_ablated = tester._calculate_metrics_with_truth_data(
            query_id=query_id,
            results=empty_results,  # No results (as expected for ablated)
            truth_data=empty_truth_data,  # Empty truth data - expect nothing
            collection_name=collection_name,
            is_ablated=True  # This is the key - it's ablated so our fix applies
        )

        # Verify the metrics are correct for this case (perfect scores)
        if metrics_ablated.precision != 1.0 or metrics_ablated.recall != 1.0 or metrics_ablated.f1_score != 1.0:
            logger.error(f"Incorrect metrics for ablated+empty collection: P={metrics_ablated.precision}, R={metrics_ablated.recall}, F1={metrics_ablated.f1_score}")
            return False

        logger.info("Empty truth data metrics for ablated collection: 1.0/1.0/1.0 ✓")

        # Test Case 2: Non-ablated collection with empty truth data but some results
        # This is a different case - if we're not ablated but have results when truth data is empty,
        # these are all false positives, so precision should be 0.0
        non_empty_results = [{"_key": "result1"}, {"_key": "result2"}]

        logger.info("Testing metrics calculation with empty truth data for non-ablated collection...")
        metrics_non_ablated = tester._calculate_metrics_with_truth_data(
            query_id=query_id,
            results=non_empty_results,  # Some results found
            truth_data=empty_truth_data,  # Empty truth data
            collection_name=collection_name,
            is_ablated=False  # Not ablated
        )

        # For a non-ablated collection, any results with empty truth list are all false positives
        # So precision should be 0.0, recall is 0/0 which is undefined but set to 0.0
        # Check if correct
        if metrics_non_ablated.precision != 0.0:
            logger.error(f"Incorrect precision for non-ablated+empty: expected 0.0, got {metrics_non_ablated.precision}")
            return False

        logger.info("Non-ablated empty truth metrics correct ✓")

        logger.info("Empty truth data metrics calculation test passed!")
        logger.info("All empty truth data handling tests passed!")

        return True

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False
    finally:
        # Clean up
        if "ABLATION_SKIP_ENTITY_VALIDATION" in os.environ:
            del os.environ["ABLATION_SKIP_ENTITY_VALIDATION"]

        # Clean up truth data from database
        try:
            if tester.db and tester.db.has_collection(tester.TRUTH_COLLECTION):
                tester.db.collection(tester.TRUTH_COLLECTION).delete(str(query_id))
                logger.info(f"Cleaned up test truth data for query {query_id}")
        except Exception as e:
            logger.warning(f"Failed to clean up test data: {e}")

        logger.info("Test completed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
