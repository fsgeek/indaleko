#!/usr/bin/env python3
"""
Simple ablation test to debug the ablation framework.

This script runs a simplified ablation test to verify that the basic framework
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
    """Run a simple ablation test."""
    logger.info("Starting simple ablation test")
    
    # Clear existing truth data
    logger.info("Clearing existing truth data...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        logger.info(f"Cleared collection {truth_collection}")
    
    # Create an AblationTester instance
    tester = AblationTester()
    
    # Define collections for testing
    collections = [
        "AblationMusicActivity",
        "AblationLocationActivity",
    ]
    
    # Define query IDs for each collection
    query_ids = {
        "AblationMusicActivity": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "AblationLocationActivity": uuid.UUID("00000000-0000-0000-0000-000000000002"),
    }
    logger.info(f"Using separate query IDs for each collection")
    
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
        # Create truth data for each collection with its own query ID
        for collection_name, query_id in query_ids.items():
            logger.info(f"Processing {collection_name} with query ID {query_id}")
            
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
        
        # Run ablation tests for each collection separately - NOT using run_ablation_test yet
        # Instead, test direct execution first
        
        # Test both collections normally (no ablation)
        for collection_name, query_id in query_ids.items():
            logger.info(f"Testing normal execution for {collection_name}")
            
            results, execution_time, aql_query = tester.execute_query(
                query_id=query_id,
                query=query_text,  # Parameter is named 'query' not 'query_text'
                collection_name=collection_name,
                limit=10,
            )
            
            logger.info(f"Normal query returned {len(results)} results from {collection_name}")
            
            # Calculate metrics
            metrics = tester.calculate_metrics(query_id, results, collection_name)
            logger.info(f"Metrics for {collection_name}: precision={metrics.precision:.4f}, recall={metrics.recall:.4f}, f1={metrics.f1_score:.4f}")
        
        # Test ablation of each collection individually
        for collection_name in collections:
            logger.info(f"Testing ablation of {collection_name}")
            
            # Ablate the collection
            tester.ablate_collection(collection_name)
            logger.info(f"Successfully ablated {collection_name}")
            
            # Test all collections with this one ablated
            for test_collection, test_query_id in query_ids.items():
                logger.info(f"Testing {test_collection} with {collection_name} ablated")
                
                results, execution_time, aql_query = tester.execute_query(
                    query_id=test_query_id,
                    query=query_text,  # Parameter is named 'query' not 'query_text'
                    collection_name=test_collection,
                    limit=10,
                )
                
                logger.info(f"Query returned {len(results)} results from {test_collection}")
                
                # Calculate metrics
                metrics = tester.calculate_metrics(test_query_id, results, test_collection)
                logger.info(f"Metrics for {test_collection}: precision={metrics.precision:.4f}, recall={metrics.recall:.4f}, f1={metrics.f1_score:.4f}")
            
            # Restore the collection
            tester.restore_collection(collection_name)
            logger.info(f"Successfully restored {collection_name}")
        
        # Now try the actual run_ablation_test function
        logger.info("Running full ablation test using run_ablation_test()...")
        
        # Run an ablation test for the first collection
        collection_name = "AblationMusicActivity"
        query_id = query_ids[collection_name]
        
        results = tester.run_ablation_test(
            config=config,
            query_id=query_id,
            query_text=query_text,
        )
        
        # Print the results
        logger.info("Ablation test completed for AblationMusicActivity")
        for key, result in results.items():
            logger.info(f"{key}: precision={result.precision:.4f}, recall={result.recall:.4f}, f1={result.f1_score:.4f}")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error running ablation test: {e}")
        return 1
    
    finally:
        # Ensure we restore any ablated collections
        for collection_name in collections:
            if hasattr(tester, 'ablated_collections') and tester.ablated_collections.get(collection_name, False):
                logger.info(f"Restoring ablated collection {collection_name}")
                tester.restore_collection(collection_name)

if __name__ == "__main__":
    sys.exit(main())