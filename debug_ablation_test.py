#!/usr/bin/env python3
"""
Minimal test script to debug issues with the AblationTester.
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
import os

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from research.ablation.ablation_tester import AblationTester
from research.ablation.run_comprehensive_ablation import setup_logging

def main():
    # Set up logging
    setup_logging(verbose=True)
    logger = logging.getLogger("debug_ablation_test")
    
    logger.info("Starting AblationTester debug test")
    
    try:
        # Create an AblationTester instance
        logger.info("Creating AblationTester instance")
        tester = AblationTester()
        logger.info("AblationTester instance created successfully")
        
        # Get a list of available collections
        logger.info("Checking available collections")
        available_collections = []
        for collection_name in [
            "AblationMusicActivity",
            "AblationLocationActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity"
        ]:
            if tester.db.has_collection(collection_name):
                available_collections.append(collection_name)
                logger.info(f"  Collection {collection_name} is available")
        
        if not available_collections:
            logger.error("No collections found, cannot proceed")
            return 1
            
        # Choose the first collection for testing
        test_collection = available_collections[0]
        logger.info(f"Using collection {test_collection} for testing")
        
        # Generate a simple query ID and text
        query_id = uuid.uuid4()
        query_text = f"Find items in {test_collection}"
        logger.info(f"Test query: ID={query_id}, text='{query_text}'")
        
        # Get entities from the test collection
        logger.info(f"Getting entities from {test_collection}")
        try:
            cursor = tester.db.aql.execute(
                f"""
                FOR doc IN {test_collection}
                LIMIT 5
                RETURN doc._key
                """
            )
            entity_keys = list(cursor)
            logger.info(f"Found {len(entity_keys)} entities: {entity_keys}")
        except Exception as e:
            logger.error(f"Failed to get entities: {e}")
            return 1
            
        if not entity_keys:
            logger.error("No entities found, cannot proceed")
            return 1
            
        # Store truth data
        logger.info("Storing truth data")
        unified_truth_data = {test_collection: entity_keys}
        try:
            tester.store_unified_truth_data(query_id, unified_truth_data)
            logger.info("Truth data stored successfully")
        except Exception as e:
            logger.error(f"Failed to store truth data: {e}")
            logger.exception("Traceback:")
            return 1
            
        # Execute baseline query
        logger.info("Executing baseline query")
        try:
            results, execution_time, aql_query = tester.execute_query(
                query_id, query_text, test_collection, 100, []
            )
            logger.info(f"Query results: {len(results)} items")
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            logger.exception("Traceback:")
            return 1
            
        # Calculate baseline metrics
        logger.info("Calculating baseline metrics")
        try:
            metrics = tester.calculate_metrics(query_id, results, test_collection)
            logger.info(f"Baseline metrics: precision={metrics.precision:.4f}, recall={metrics.recall:.4f}, f1={metrics.f1_score:.4f}")
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            logger.exception("Traceback:")
            return 1
        
        # Success!
        logger.info("Debug test completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.exception("Traceback:")
        return 1
        
if __name__ == "__main__":
    sys.exit(main())