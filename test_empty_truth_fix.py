#!/usr/bin/env python3
"""Test script for empty truth data fixes in the ablation framework."""

import logging
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

    # Set up truth data
    truth_data = {
        # Populated data
        "AblationMusicActivity": ["music_doc_1", "music_doc_2", "music_doc_3"],
        # Empty but valid data
        "AblationLocationActivity": [],
        # Populated data
        "AblationTaskActivity": ["task_doc_1", "task_doc_2"],
        # Empty but valid data
        "AblationCollaborationActivity": [],
        # Populated data
        "AblationStorageActivity": ["storage_doc_1"]
    }

    # Step 3: Store the truth data
    try:
        logger.info("Storing unified truth data with empty collection lists")
        tester.store_unified_truth_data(query_id, truth_data)
        logger.info("Successfully stored unified truth data")
    except Exception as e:
        logger.error(f"Failed to store truth data: {e}")
        return False

    # Step 4: Verify the truth data was stored correctly
    unified_truth = tester.get_unified_truth_data(query_id)
    if not unified_truth:
        logger.error("Failed to retrieve unified truth data")
        return False

    # Check that our empty collections are properly stored and retrieved
    for collection, entities in unified_truth.items():
        if collection in truth_data:
            expected_count = len(truth_data[collection])
            actual_count = len(entities)
            logger.info(f"Collection {collection}: Expected {expected_count}, Got {actual_count}")
            if expected_count != actual_count:
                logger.error(f"Truth data count mismatch for {collection}")
                return False

    # Step 5: Test collection-specific truth data retrieval
    for collection in collections_to_test:
        collection_truth = tester.get_collection_truth_data(query_id, collection)
        logger.info(f"Retrieved truth data for {collection}: {len(collection_truth)} entities")

    # Step 6: Test ablation with empty collections
    config = AblationConfig(
        collections_to_ablate=collections_to_test,
        query_limit=10,
        include_metrics=True,
        verbose=True
    )

    query_text = "Find tasks with music by Taylor Swift"

    # Run ablation test
    logger.info(f"Running ablation test with query: {query_text}")
    results = tester.run_ablation_test(config, query_id, query_text)

    # Step 7: Analyze and print results
    logger.info("Test results:")
    for impact_key, metrics in results.items():
        logger.info(f"{impact_key}:")
        logger.info(f"  Precision: {metrics.precision:.4f}")
        logger.info(f"  Recall: {metrics.recall:.4f}")
        logger.info(f"  F1 Score: {metrics.f1_score:.4f}")
        logger.info(f"  True Positives: {metrics.true_positives}")
        logger.info(f"  False Positives: {metrics.false_positives}")
        logger.info(f"  False Negatives: {metrics.false_negatives}")

    # Clean up after the test
    tester.cleanup()

    logger.info("Test completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
