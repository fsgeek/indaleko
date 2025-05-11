#!/usr/bin/env python3
"""
Test script for ablation with local logging.
"""

import logging
import os
import sys
import uuid
from pathlib import Path
import random

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from research.ablation.ablation_tester import AblationTester

# Configure local logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ablation_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_ablation_local")

def main():
    """
    Test ablation with local logging.
    """
    try:
        logger.info("Creating AblationTester instance")
        tester = AblationTester()
        
        # Check for AblationMusicActivity collection
        collection_name = "AblationMusicActivity"
        if not tester.db.has_collection(collection_name):
            logger.error(f"Collection {collection_name} does not exist")
            return 1
        
        # Get all Taylor Swift songs
        logger.info("Getting all Taylor Swift songs")
        aql_query = f"""
        FOR doc IN {collection_name}
        FILTER doc.artist == "Taylor Swift"
        RETURN doc
        """
        cursor = tester.db.aql.execute(aql_query)
        swift_docs = list(cursor)
        logger.info(f"Found {len(swift_docs)} Taylor Swift songs")
        
        if not swift_docs:
            logger.error("No Taylor Swift songs found, cannot proceed with test")
            return 1
        
        # Create a query ID
        query_id = uuid.uuid4()
        query_text = "Find music by Taylor Swift"
        logger.info(f"Using query ID: {query_id}")
        logger.info(f"Using query text: '{query_text}'")
        
        # Use 5 random Taylor Swift songs as truth data
        random.shuffle(swift_docs)
        truth_docs = swift_docs[:5]
        logger.info(f"Using {len(truth_docs)} Taylor Swift songs as truth data")
        
        # Extract document keys
        truth_keys = [doc["_key"] for doc in truth_docs]
        logger.info(f"Truth keys: {truth_keys}")
        
        # Store unified truth data
        unified_truth_data = {collection_name: truth_keys}
        logger.info("Storing unified truth data")
        result = tester.store_unified_truth_data(query_id, unified_truth_data)
        logger.info(f"Store result: {result}")
        
        # Run the query
        logger.info("Executing query")
        results, execution_time, aql_query = tester.execute_query(
            query_id, query_text, collection_name, 100, []
        )
        logger.info(f"Query execution completed in {execution_time}ms")
        logger.info(f"Got {len(results)} results")
        logger.info(f"AQL Query: {aql_query}")
        
        # Calculate metrics
        logger.info("Calculating metrics")
        metrics = tester.calculate_metrics(query_id, results, collection_name)
        logger.info(f"Precision: {metrics.precision:.4f}")
        logger.info(f"Recall: {metrics.recall:.4f}")
        logger.info(f"F1 Score: {metrics.f1_score:.4f}")
        logger.info(f"True Positives: {metrics.true_positives}")
        logger.info(f"False Positives: {metrics.false_positives}")
        logger.info(f"False Negatives: {metrics.false_negatives}")
        
        # Ablate the collection
        logger.info(f"Ablating collection {collection_name}")
        tester.ablate_collection(collection_name)
        
        # Run the query on the ablated collection
        logger.info("Executing query on ablated collection")
        ablated_results, ablated_time, ablated_query = tester.execute_query(
            query_id, query_text, collection_name, 100, []
        )
        logger.info(f"Ablated query execution completed in {ablated_time}ms")
        logger.info(f"Got {len(ablated_results)} results from ablated collection")
        
        # Calculate metrics for ablated collection
        logger.info("Calculating metrics for ablated collection")
        ablated_metrics = tester.calculate_metrics(query_id, ablated_results, collection_name)
        logger.info(f"Ablated Precision: {ablated_metrics.precision:.4f}")
        logger.info(f"Ablated Recall: {ablated_metrics.recall:.4f}")
        logger.info(f"Ablated F1 Score: {ablated_metrics.f1_score:.4f}")
        logger.info(f"Ablated True Positives: {ablated_metrics.true_positives}")
        logger.info(f"Ablated False Positives: {ablated_metrics.false_positives}")
        logger.info(f"Ablated False Negatives: {ablated_metrics.false_negatives}")
        
        # Restore the collection
        logger.info(f"Restoring collection {collection_name}")
        tester.restore_collection(collection_name)
        
        # Return success
        logger.info("Test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.exception("Traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())