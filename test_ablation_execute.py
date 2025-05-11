#!/usr/bin/env python3
"""
Test script for ablation execution and metrics calculation.
"""

import logging
import sys
import uuid
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_ablation_execute")

def main():
    """Test ablation execution and metrics calculation."""
    try:
        logger.info("Creating AblationTester")
        tester = AblationTester()
        
        # Get a list of collections to test with
        collections = []
        logger.info("Checking for collections")
        for collection_name in [
            "AblationMusicActivity",
            "AblationLocationActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity"
        ]:
            if tester.db.has_collection(collection_name):
                collections.append(collection_name)
                logger.info(f"Found collection: {collection_name}")
        
        if not collections:
            logger.error("No ablation collections found")
            return 1
            
        # Get a test collection
        test_collection = collections[0]
        logger.info(f"Using collection: {test_collection}")
        
        # Get a few entities from the collection
        logger.info(f"Getting entities from collection: {test_collection}")
        aql_query = f"""
        FOR doc IN {test_collection}
        LIMIT 5
        RETURN doc._key
        """
        cursor = tester.db.aql.execute(aql_query)
        entity_keys = list(cursor)
        logger.info(f"Found entities: {entity_keys}")
        
        # Generate a query ID
        query_id = uuid.uuid4()
        logger.info(f"Generated query ID: {query_id}")
        
        # Create unified truth data
        unified_truth_data = {
            test_collection: entity_keys
        }
        logger.info(f"Created unified truth data: {unified_truth_data}")
        
        # Store the truth data
        logger.info("Storing unified truth data")
        result = tester.store_unified_truth_data(query_id, unified_truth_data)
        logger.info(f"Result of storing truth data: {result}")
        
        # Generate a query text
        query_text = "Find music by Taylor Swift"
        if "Location" in test_collection:
            query_text = "Find activities at Home"
        elif "Task" in test_collection:
            query_text = "Find tasks related to work"
        elif "Collaboration" in test_collection:
            query_text = "Find meetings about project status"
        elif "Storage" in test_collection:
            query_text = "Find files related to projects"
        elif "Media" in test_collection:
            query_text = "Find videos watched recently"
            
        logger.info(f"Using query text: {query_text}")
        
        # Execute the query
        logger.info("Executing query")
        results, execution_time, aql_query = tester.execute_query(
            query_id, query_text, test_collection, 100, []
        )
        logger.info(f"Query execution completed in {execution_time}ms")
        logger.info(f"Got {len(results)} results")
        logger.info(f"AQL Query: {aql_query}")
        
        # Calculate metrics
        logger.info("Calculating metrics")
        metrics = tester.calculate_metrics(query_id, results, test_collection)
        logger.info(f"Precision: {metrics.precision:.4f}")
        logger.info(f"Recall: {metrics.recall:.4f}")
        logger.info(f"F1 Score: {metrics.f1_score:.4f}")
        logger.info(f"True Positives: {metrics.true_positives}")
        logger.info(f"False Positives: {metrics.false_positives}")
        logger.info(f"False Negatives: {metrics.false_negatives}")
        
        # Ablate the collection
        logger.info(f"Ablating collection {test_collection}")
        tester.ablate_collection(test_collection)
        
        # Execute the query again on the ablated collection
        logger.info("Executing query on ablated collection")
        ablated_results, ablated_time, ablated_query = tester.execute_query(
            query_id, query_text, test_collection, 100, []
        )
        logger.info(f"Ablated query execution completed in {ablated_time}ms")
        logger.info(f"Got {len(ablated_results)} results from ablated collection")
        logger.info(f"Ablated AQL Query: {ablated_query}")
        
        # Calculate metrics for ablated collection
        logger.info("Calculating metrics for ablated collection")
        ablated_metrics = tester.calculate_metrics(query_id, ablated_results, test_collection)
        logger.info(f"Ablated Precision: {ablated_metrics.precision:.4f}")
        logger.info(f"Ablated Recall: {ablated_metrics.recall:.4f}")
        logger.info(f"Ablated F1 Score: {ablated_metrics.f1_score:.4f}")
        logger.info(f"Ablated True Positives: {ablated_metrics.true_positives}")
        logger.info(f"Ablated False Positives: {ablated_metrics.false_positives}")
        logger.info(f"Ablated False Negatives: {ablated_metrics.false_negatives}")
        
        # Restore the collection
        logger.info(f"Restoring collection {test_collection}")
        tester.restore_collection(test_collection)
        
        # Print baseline and ablated metrics for comparison
        logger.info("\nMetrics Comparison")
        logger.info("Metric       | Baseline  | Ablated")
        logger.info("-------------|-----------|--------")
        logger.info(f"Precision    | {metrics.precision:.4f}     | {ablated_metrics.precision:.4f}")
        logger.info(f"Recall       | {metrics.recall:.4f}     | {ablated_metrics.recall:.4f}")
        logger.info(f"F1 Score     | {metrics.f1_score:.4f}     | {ablated_metrics.f1_score:.4f}")
        logger.info(f"True Pos     | {metrics.true_positives}         | {ablated_metrics.true_positives}")
        logger.info(f"False Pos    | {metrics.false_positives}         | {ablated_metrics.false_positives}")
        logger.info(f"False Neg    | {metrics.false_negatives}         | {ablated_metrics.false_negatives}")
        
        # Calculate binary vs non-binary metrics
        precision_values = [metrics.precision, ablated_metrics.precision]
        recall_values = [metrics.recall, ablated_metrics.recall]
        
        binary_precision_count = sum(1 for p in precision_values if p == 0.0 or p == 1.0)
        binary_recall_count = sum(1 for r in recall_values if r == 0.0 or r == 1.0)
        
        logger.info("\nBinary Metrics Analysis")
        logger.info(f"Precision values: {precision_values}")
        logger.info(f"Binary precision values: {binary_precision_count} out of {len(precision_values)}")
        
        logger.info(f"Recall values: {recall_values}")
        logger.info(f"Binary recall values: {binary_recall_count} out of {len(recall_values)}")
        
        if binary_precision_count < len(precision_values) or binary_recall_count < len(recall_values):
            logger.info("✅ SUCCESS: Found non-binary precision/recall values")
        else:
            logger.warning("⚠️ WARNING: All precision/recall values are binary (0.0 or 1.0)")
        
        logger.info("Test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected exception: {str(e)}")
        logger.exception("Traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())