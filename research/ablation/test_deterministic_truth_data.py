#!/usr/bin/env python3
"""
Test deterministic truth data generation in ablation framework.

This script verifies that our fixes for deterministic truth data generation work correctly
by ensuring that the same query IDs always generate the same truth data, across multiple runs.
"""

import logging
import sys
import uuid

from db.db_config import IndalekoDBConfig
from research.ablation.ablation_tester import AblationTester
from research.ablation.utils.uuid_utils import generate_deterministic_uuid


def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def get_deterministic_entities(db, collection_name: str, seed_value: int, count: int = 5) -> list[str]:
    """
    Get deterministic entities using the same approach as in experiment_runner.py.

    Args:
        db: ArangoDB database connection
        collection_name: Name of collection to get entities from
        seed_value: Seed value for deterministic selection
        count: Number of entities to select

    Returns:
        List of entity keys
    """
    logger = logging.getLogger(__name__)

    # Calculate a fixed offset based on the seed value
    fixed_offset = seed_value % 20

    logger.info(f"Using seed {seed_value} with fixed offset {fixed_offset} for {collection_name}")

    # Use the same deterministic query as in experiment_runner.py
    aql_query = f"""
    FOR doc IN {collection_name}
    SORT doc._key ASC  /* Use stable ascending sort by document key */
    LIMIT {fixed_offset}, {count}  /* Take exactly {count} entities with fixed offset */
    RETURN doc._key
    """

    cursor = db.aql.execute(aql_query)
    entity_keys = [doc_key for doc_key in cursor]

    logger.info(f"Selected {len(entity_keys)} deterministic entities for {collection_name}")

    return entity_keys


def test_deterministic_generation(collection_name: str, num_iterations: int = 3) -> bool:
    """
    Test whether truth data generation is deterministic.

    Args:
        collection_name: Name of the collection to test
        num_iterations: Number of iterations to run

    Returns:
        bool: True if all iterations produced the same truth data, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Testing deterministic truth data generation for {collection_name}")

    # Create a database connection
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()

    # Check if the collection exists
    if not db.has_collection(collection_name):
        logger.error(f"Collection {collection_name} does not exist")
        return False

    # Create a truth collection if it doesn't exist
    truth_collection = "AblationQueryTruth"
    if not db.has_collection(truth_collection):
        db.create_collection(truth_collection)
        logger.info(f"Created truth collection {truth_collection}")

    # Always clear the truth collection first
    db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
    logger.info(f"Cleared truth collection {truth_collection}")

    # Create a unique query ID base for this test run
    base_id = str(uuid.uuid4())

    # Create an AblationTester instance
    tester = AblationTester()

    # Track all truth data across iterations
    all_truth_data = []

    # Run multiple iterations to test determinism
    for i in range(num_iterations):
        logger.info(f"=== Iteration {i+1}/{num_iterations} ===")

        # Generate a deterministic query ID
        # Similar to experiment_runner.py: fixed_query:{collection}:{i}:{seed}
        query_id = generate_deterministic_uuid(f"fixed_query:{collection_name}:{i}:42")
        logger.info(f"Using deterministic query ID: {query_id}")

        # Convert the query ID to a deterministic seed
        seed_str = str(query_id).replace("-", "")
        seed_value = int(seed_str[:8], 16)

        # Get deterministic entities for this collection and seed
        entity_keys = get_deterministic_entities(db, collection_name, seed_value)

        if not entity_keys:
            logger.error(f"No entities found in collection {collection_name}")
            return False

        logger.info(f"Selected {len(entity_keys)} entities as truth data: {entity_keys}")

        # Store in the truth collection
        tester.store_truth_data(query_id, collection_name, entity_keys)

        # Re-fetch the truth data to confirm it was stored
        truth_data = tester.get_truth_data(query_id, collection_name)

        if not truth_data:
            logger.error(f"Failed to store truth data for {query_id} in {collection_name}")
            return False

        logger.info(f"Retrieved {len(truth_data)} truth data entries: {truth_data}")

        # Track this truth data for comparison
        all_truth_data.append((query_id, truth_data))

    # Clear AblationQueryTruth collection again
    db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
    logger.info(f"Cleared truth collection {truth_collection}")

    # Now run the same process again and verify we get the same truth data
    logger.info("=== Running verification pass to confirm deterministic behavior ===")

    all_verified = True

    for i, (original_query_id, original_truth_data) in enumerate(all_truth_data):
        logger.info(f"Verification {i+1}/{len(all_truth_data)} for query ID {original_query_id}")

        # Calculate seed value from query ID (same as before)
        seed_str = str(original_query_id).replace("-", "")
        seed_value = int(seed_str[:8], 16)

        # Get deterministic entities using same method
        entity_keys = get_deterministic_entities(db, collection_name, seed_value)

        # Compare with original truth data
        if set(entity_keys) != original_truth_data:
            logger.error("Verification FAILED: Truth data is different!")
            logger.error(f"Original: {original_truth_data}")
            logger.error(f"New: {set(entity_keys)}")
            all_verified = False
        else:
            logger.info("Verification PASSED: Generated same truth data")

    return all_verified


def test_execution_matching(collection_name: str, num_iterations: int = 3) -> bool:
    """
    Test whether query execution correctly matches truth data.

    Args:
        collection_name: Name of the collection to test
        num_iterations: Number of iterations to run

    Returns:
        bool: True if all iterations produced correct query results, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Testing truth data matching in query execution for {collection_name}")

    # Create a database connection
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()

    # Check if the collection exists
    if not db.has_collection(collection_name):
        logger.error(f"Collection {collection_name} does not exist")
        return False

    # Create a truth collection if it doesn't exist
    truth_collection = "AblationQueryTruth"
    if not db.has_collection(truth_collection):
        db.create_collection(truth_collection)
        logger.info(f"Created truth collection {truth_collection}")

    # Always clear the truth collection first
    db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
    logger.info(f"Cleared truth collection {truth_collection}")

    # Create an AblationTester instance
    tester = AblationTester()

    # Create a test query based on collection type
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

    # Track success across iterations
    all_tests_passed = True

    # Run multiple iterations
    for i in range(num_iterations):
        logger.info(f"=== Iteration {i+1}/{num_iterations} ===")

        # Generate a deterministic query ID
        query_id = generate_deterministic_uuid(f"fixed_query:{collection_name}:{i}:42")
        logger.info(f"Using deterministic query ID: {query_id}")

        # Convert the query ID to a deterministic seed
        seed_str = str(query_id).replace("-", "")
        seed_value = int(seed_str[:8], 16)

        # Get deterministic entities for this collection and seed
        entity_keys = get_deterministic_entities(db, collection_name, seed_value)

        if not entity_keys:
            logger.error(f"No entities found in collection {collection_name}")
            all_tests_passed = False
            continue

        logger.info(f"Selected {len(entity_keys)} entities as truth data: {entity_keys}")

        # Store in the truth collection
        tester.store_truth_data(query_id, collection_name, entity_keys)

        # Execute the query
        results, execution_time, aql_query = tester.execute_query(query_id, query_text, collection_name)

        logger.info(f"Query execution completed in {execution_time}ms")
        logger.info(f"Query returned {len(results)} results")
        logger.info(f"AQL query: {aql_query}")

        # Calculate metrics
        metrics = tester.calculate_metrics(query_id, results, collection_name)

        logger.info(
            f"Metrics: precision={metrics.precision:.4f}, recall={metrics.recall:.4f}, f1_score={metrics.f1_score:.4f}",
        )
        logger.info(
            f"True positives: {metrics.true_positives}, False positives: {metrics.false_positives}, False negatives: {metrics.false_negatives}",
        )

        # Verify that all truth data is matched in results
        expected_match_count = len(entity_keys)
        actual_match_count = metrics.true_positives

        if actual_match_count < expected_match_count:
            logger.error(
                f"FAILED: Not all truth data matched! Expected {expected_match_count}, got {actual_match_count}",
            )
            # Identify which truth entities are missing
            result_keys = set(doc.get("_key") for doc in results)
            missing_keys = set(entity_keys) - result_keys
            logger.error(f"Missing keys: {missing_keys}")
            all_tests_passed = False
        else:
            logger.info(f"SUCCESS: All {expected_match_count} truth entities matched correctly!")

    # Clean up
    db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
    logger.info(f"Cleaned up truth collection {truth_collection}")

    return all_tests_passed


def test_cross_run_consistency() -> bool:
    """
    Test consistency across independent tester instances.

    This test simulates what happens in the comprehensive experiment across multiple rounds.

    Returns:
        bool: True if test passes, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("Testing cross-run consistency with multiple tester instances")

    # Pick a test collection
    collection_name = "AblationMusicActivity"

    # Create a database connection to check if collection exists
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()

    if not db.has_collection(collection_name):
        logger.error(f"Collection {collection_name} does not exist")
        return False

    # Always clear the truth collection first
    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        logger.info(f"Cleared truth collection {truth_collection}")

    # Generate a fixed query ID
    query_id = generate_deterministic_uuid(f"fixed_query:{collection_name}:0:42")
    logger.info(f"Using deterministic query ID: {query_id}")

    # First run: Create truth data and run query
    logger.info("=== First run: creating truth data ===")
    tester1 = AblationTester()

    # Convert the query ID to a deterministic seed
    seed_str = str(query_id).replace("-", "")
    seed_value = int(seed_str[:8], 16)

    # Get deterministic entities
    entity_keys = get_deterministic_entities(db, collection_name, seed_value)

    if not entity_keys:
        logger.error(f"No entities found in collection {collection_name}")
        return False

    logger.info(f"Selected {len(entity_keys)} entities as truth data: {entity_keys}")

    # Store truth data with first tester
    tester1.store_truth_data(query_id, collection_name, entity_keys)

    # Execute query with first tester
    query_text = "Find all songs by Taylor Swift"
    results1, _, _ = tester1.execute_query(query_id, query_text, collection_name)

    # Calculate metrics with first tester
    metrics1 = tester1.calculate_metrics(query_id, results1, collection_name)

    logger.info(f"First run: {len(results1)} results, {metrics1.true_positives} true positives")

    # Second run: Create a new tester instance (simulates a new round)
    logger.info("=== Second run: using existing truth data ===")
    tester2 = AblationTester()

    # Execute query with second tester
    results2, _, _ = tester2.execute_query(query_id, query_text, collection_name)

    # Calculate metrics with second tester
    metrics2 = tester2.calculate_metrics(query_id, results2, collection_name)

    logger.info(f"Second run: {len(results2)} results, {metrics2.true_positives} true positives")

    # Verify metrics are the same between runs
    if metrics1.true_positives != metrics2.true_positives:
        logger.error(
            f"FAILED: Different number of true positives between runs! {metrics1.true_positives} vs {metrics2.true_positives}",
        )
        return False

    if metrics1.false_positives != metrics2.false_positives:
        logger.error(
            f"FAILED: Different number of false positives between runs! {metrics1.false_positives} vs {metrics2.false_positives}",
        )
        return False

    if metrics1.false_negatives != metrics2.false_negatives:
        logger.error(
            f"FAILED: Different number of false negatives between runs! {metrics1.false_negatives} vs {metrics2.false_negatives}",
        )
        return False

    logger.info("SUCCESS: Both runs produced identical metrics!")

    # Clean up
    db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
    logger.info(f"Cleaned up truth collection {truth_collection}")

    return True


def main():
    """Main entry point for the test script."""
    logger = setup_logging()
    logger.info("Starting deterministic truth data generation tests")

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Test deterministic truth data generation in ablation framework")
    parser.add_argument("--collection", type=str, help="Collection to test")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations for tests")
    parser.add_argument("--all-collections", action="store_true", help="Test all ablation collections")
    parser.add_argument("--test-generation", action="store_true", help="Test truth data generation")
    parser.add_argument("--test-execution", action="store_true", help="Test query execution")
    parser.add_argument("--test-cross-run", action="store_true", help="Test cross-run consistency")
    args = parser.parse_args()

    # Set default tests if none specified
    if not (args.test_generation or args.test_execution or args.test_cross_run):
        args.test_generation = True
        args.test_execution = True
        args.test_cross_run = True

    # If testing all collections, discover available collections
    if args.all_collections:
        try:
            db_config = IndalekoDBConfig()
            db = db_config.get_arangodb()
            collections = []

            # ArangoDB collections() returns a list of collection objects or dicts, not just names
            for collection in db.collections():
                # Get the collection name (handle both object and dict cases)
                if hasattr(collection, "name"):
                    collection_name = collection.name
                elif isinstance(collection, dict) and "name" in collection:
                    collection_name = collection["name"]
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
    elif args.collection:
        collections = [args.collection]
    else:
        # Default to a known collection if none specified
        collections = ["AblationMusicActivity"]

    # Track test results
    all_passed = True

    # First test cross-run consistency if requested (only needs to run once)
    if args.test_cross_run:
        logger.info("=== Testing cross-run consistency ===")
        cross_run_passed = test_cross_run_consistency()
        all_passed = all_passed and cross_run_passed

        if cross_run_passed:
            logger.info("✅ Cross-run consistency test passed!")
        else:
            logger.error("❌ Cross-run consistency test failed!")

    # Run tests for each collection
    for collection_name in collections:
        logger.info(f"=== Testing collection {collection_name} ===")

        if args.test_generation:
            logger.info(f"=== Testing deterministic truth data generation for {collection_name} ===")
            generation_passed = test_deterministic_generation(collection_name, args.iterations)
            all_passed = all_passed and generation_passed

            if generation_passed:
                logger.info(f"✅ Deterministic generation test passed for {collection_name}!")
            else:
                logger.error(f"❌ Deterministic generation test failed for {collection_name}!")

        if args.test_execution:
            logger.info(f"=== Testing query execution with truth data for {collection_name} ===")
            execution_passed = test_execution_matching(collection_name, args.iterations)
            all_passed = all_passed and execution_passed

            if execution_passed:
                logger.info(f"✅ Query execution test passed for {collection_name}!")
            else:
                logger.error(f"❌ Query execution test failed for {collection_name}!")

    if all_passed:
        logger.info("✅ All tests passed! Deterministic truth data generation is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Issues remain with deterministic truth data generation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
