#!/usr/bin/env python3
"""
Minimal ablation test to debug the ablation framework.

This script runs a minimal ablation test to verify that the basic framework
is working correctly, without the complexity of the comprehensive experiment.
"""

import logging
import sys
import uuid
from pathlib import Path

from db.db_config import IndalekoDBConfig
from research.ablation.ablation_tester import AblationConfig, AblationTester
from research.ablation.data_sanity_checker import DataSanityChecker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def main():
    """Run a minimal ablation test."""
    logger.info("Starting minimal ablation test")

    # Clear existing truth data
    logger.info("Clearing existing truth data...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()

    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        logger.info(f"Cleared collection {truth_collection}")

    # First run a data sanity check
    checker = DataSanityChecker(fail_fast=False)
    all_checks_passed = checker.run_all_checks()

    if not all_checks_passed:
        logger.warning("Some data sanity checks failed - continuing anyway")

    # Create an AblationTester instance
    tester = AblationTester()

    # Define collections for testing
    collections = [
        "AblationMusicActivity",
        "AblationLocationActivity",
    ]

    # Generate a query ID - use a deterministic ID for reproducibility
    query_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    logger.info(f"Using query ID: {query_id}")

    # Create a test query
    query_text = "Find songs listened to in New York"
    logger.info(f"Using test query: {query_text}")
    
    # Define config
    config = AblationConfig(
        collections_to_ablate=collections,
        query_limit=10,
        include_metrics=True,
        include_execution_time=True,
        verbose=True,
    )
    
    try:
        # Try to get existing truth data for the music activity collection
        collection_name = "AblationMusicActivity"
        
        truth_data = tester.get_truth_data(query_id, collection_name)
        if not truth_data:
            logger.info(f"No truth data for query {query_id} in collection {collection_name}")
            logger.info("Creating some test truth data...")
            
            # Get a few entities from the collection
            cursor = tester.db.aql.execute(
                f"""
                FOR doc IN {collection_name}
                SORT doc._key
                LIMIT 5
                RETURN doc._key
                """
            )
            entity_keys = [doc for doc in cursor]
            
            if entity_keys:
                # Store the truth data
                tester.store_truth_data(query_id, collection_name, entity_keys)
                logger.info(f"Created truth data for {collection_name} with {len(entity_keys)} entities")
            else:
                logger.warning(f"No entities found in collection {collection_name}")
        
        # Do the same for location activity
        collection_name = "AblationLocationActivity"
        
        truth_data = tester.get_truth_data(query_id, collection_name)
        if not truth_data:
            logger.info(f"No truth data for query {query_id} in collection {collection_name}")
            logger.info("Creating some test truth data...")
            
            cursor = tester.db.aql.execute(
                f"""
                FOR doc IN {collection_name}
                SORT doc._key
                LIMIT 5
                RETURN doc._key
                """
            )
            entity_keys = [doc for doc in cursor]
            
            if entity_keys:
                tester.store_truth_data(query_id, collection_name, entity_keys)
                logger.info(f"Created truth data for {collection_name} with {len(entity_keys)} entities")
            else:
                logger.warning(f"No entities found in collection {collection_name}")
        
        # Run the ablation test
        logger.info("Running ablation test...")
        results = tester.run_ablation_test(
            config=config,
            query_id=query_id,
            query_text=query_text,
        )
        
        # Print the results
        logger.info("Ablation test completed successfully")
        for key, result in results.items():
            logger.info(f"{key}: precision={result.precision:.2f}, recall={result.recall:.2f}, f1={result.f1_score:.2f}")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error running ablation test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())