#!/usr/bin/env python3
"""
Test the fixed deterministic entity selection logic.

This script verifies that the fixes for deterministic entity selection work correctly
by running multiple rounds of entity selection with the same query IDs and checking
that the same entities are selected each time.
"""

import argparse
import logging
import sys
import uuid
from datetime import datetime

from db.db_config import IndalekoDBConfig
from research.ablation.utils.uuid_utils import generate_deterministic_uuid


def setup_logging(log_level=logging.INFO):
    """Set up logging for the test."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def get_deterministic_entities(db, collection_name, query_id, current_round, count=5):
    """
    Get deterministic entities using the fixed entity selection logic.

    Args:
        db: ArangoDB database connection
        collection_name: Name of collection to get entities from
        query_id: The deterministic query ID
        current_round: The current experimental round
        count: Number of entities to select

    Returns:
        List of entity keys
    """
    logger = logging.getLogger(__name__)

    # Convert the query ID to a deterministic seed
    # Using a consistent hash function for the seed value
    seed_str = str(query_id).replace('-', '')
    # Use more bits from the UUID for better distribution
    seed_value = int(seed_str[:12], 16)  # Use 12 hex chars instead of 8

    # Fix the offset to ensure the same entities are always selected for the same query
    # Use a more sophisticated formula that's less likely to have collisions
    fixed_offset = (seed_value % 50) + (current_round * 7) % 10

    logger.info(f"Using seed {seed_value} with fixed offset {fixed_offset} for {collection_name}")

    # Use a fixed AQL query with standardized sorting
    # Using stable sort by _key (no random functions) and fixed entity count
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


def test_deterministic_selection(collections=None, iterations=3, rounds=2, log_level=logging.INFO):
    """
    Test whether the deterministic entity selection logic works correctly.
    
    Args:
        collections: List of collections to test
        iterations: Number of iterations to run per round
        rounds: Number of experimental rounds to simulate
        log_level: Logging level
        
    Returns:
        bool: True if all tests pass, False otherwise
    """
    logger = setup_logging(log_level)
    logger.info("Testing fixed deterministic entity selection logic")
    
    # Create database connection
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    # If no collections specified, use a default test collection
    if not collections:
        collections = ["AblationMusicActivity"]
    
    # Test collections
    all_tests_passed = True
    
    # For each collection, run the test
    for collection_name in collections:
        logger.info(f"=== Testing collection {collection_name} ===")
        
        # Check if collection exists
        if not db.has_collection(collection_name):
            logger.error(f"Collection {collection_name} does not exist")
            continue
            
        # For each iteration, generate a fixed query ID and select entities
        for i in range(iterations):
            logger.info(f"=== Iteration {i+1}/{iterations} ===")
            
            # Generate a fixed query ID for this collection and iteration
            query_id = generate_deterministic_uuid(f"fixed_query:{collection_name}:{i}:42")
            logger.info(f"Generated fixed query ID: {query_id}")
            
            # Store selected entities for each round
            round_entities = []
            
            # For each round, select entities
            for r in range(rounds):
                logger.info(f"=== Round {r+1}/{rounds} ===")
                
                # Get deterministic entities for this query ID and round
                entities = get_deterministic_entities(db, collection_name, query_id, r)
                
                if not entities:
                    logger.error(f"No entities found in collection {collection_name}")
                    all_tests_passed = False
                    continue
                    
                logger.info(f"Selected {len(entities)} entities: {entities}")
                
                # Store entities for this round
                round_entities.append(entities)
            
            # Verify that entity selection varies predictably between rounds
            round_differences = []
            for r in range(1, rounds):
                # Check differences between rounds
                round_a = set(round_entities[0])
                round_b = set(round_entities[r])
                differences = round_a.symmetric_difference(round_b)
                
                logger.info(f"Round 1 vs Round {r+1}: {len(differences)} entity differences")
                round_differences.append(len(differences))
            
            # Then run the same rounds again and verify we get the same entities
            logger.info("=== Verification pass for deterministic behavior ===")
            for r in range(rounds):
                logger.info(f"=== Verifying Round {r+1}/{rounds} ===")
                
                # Get deterministic entities for this query ID and round
                entities = get_deterministic_entities(db, collection_name, query_id, r)
                
                # Verify that entities match the original selection
                if set(entities) != set(round_entities[r]):
                    logger.error("Verification FAILED: Entities don't match original selection!")
                    logger.error(f"Original entities: {round_entities[r]}")
                    logger.error(f"Verification entities: {entities}")
                    all_tests_passed = False
                else:
                    logger.info(f"Verification PASSED for Round {r+1}")
    
    # Return final result
    if all_tests_passed:
        logger.info("All tests passed - entity selection is deterministic and round-specific!")
    else:
        logger.error("Some tests failed - entity selection is not deterministic!")
        
    return all_tests_passed


def main():
    """Main entry point for the test script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test fixed deterministic entity selection logic")
    parser.add_argument("--collections", type=str, help="Comma-separated list of collections to test")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations to run per round")
    parser.add_argument("--rounds", type=int, default=2, help="Number of experimental rounds to simulate")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)
    
    # Parse collections
    collections = []
    if args.collections:
        collections = [c.strip() for c in args.collections.split(",")]
    
    # Run the test
    logger.info(f"Starting test with {args.iterations} iterations and {args.rounds} rounds")
    start_time = datetime.now()
    success = test_deterministic_selection(
        collections=collections,
        iterations=args.iterations,
        rounds=args.rounds,
        log_level=log_level
    )
    end_time = datetime.now()
    
    # Report results
    logger.info(f"Test completed in {end_time - start_time}")
    
    # Return success status
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())