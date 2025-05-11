#!/usr/bin/env python3
"""
Test script that verifies the fixed binary precision/recall issue using realistic test data.
This script:
1. Gets documents matching 'Taylor Swift' from the AblationMusicActivity collection
2. Splits them into truth and non-truth sets
3. Sets up realistic truth data
4. Runs the query and verifies we get non-binary precision/recall values
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
from research.ablation.run_comprehensive_ablation import setup_logging

def main():
    """
    Test the fix for binary precision/recall issue using realistic test data.
    """
    # Set up logging
    setup_logging(verbose=True)
    logger = logging.getLogger("test_ablation_fixed")
    
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
        
        # Get some non-Taylor Swift songs for negative testing
        logger.info("Getting non-Taylor Swift songs")
        aql_query = f"""
        FOR doc IN {collection_name}
        FILTER doc.artist != "Taylor Swift"
        LIMIT 20
        RETURN doc
        """
        cursor = tester.db.aql.execute(aql_query)
        non_swift_docs = list(cursor)
        logger.info(f"Found {len(non_swift_docs)} non-Taylor Swift songs")
        
        # Create a query ID
        query_id = uuid.uuid4()
        query_text = "Find music by Taylor Swift"
        logger.info(f"Using query ID: {query_id}")
        logger.info(f"Using query text: '{query_text}'")
        
        # Now create truth data
        # For testing precision/recall, we'll use half of the Taylor Swift songs
        # This will give us partial matches for more interesting metrics
        random.shuffle(swift_docs)
        split_point = len(swift_docs) // 2
        
        truth_swift_docs = swift_docs[:split_point]
        logger.info(f"Using {len(truth_swift_docs)} Taylor Swift songs as truth data")
        
        # Extract document keys
        truth_keys = [doc["_key"] for doc in truth_swift_docs]
        logger.info(f"Truth keys: {truth_keys}")
        
        # Store unified truth data
        unified_truth_data = {collection_name: truth_keys}
        logger.info("Storing unified truth data")
        tester.store_unified_truth_data(query_id, unified_truth_data)
        
        # Run the query
        logger.info("Executing query")
        results, execution_time, aql_query = tester.execute_query(
            query_id, query_text, collection_name, 100, []
        )
        logger.info(f"Query execution completed in {execution_time}ms")
        logger.info(f"Got {len(results)} results")
        
        # Calculate metrics
        logger.info("Calculating baseline metrics")
        metrics = tester.calculate_metrics(query_id, results, collection_name)
        logger.info(f"Precision: {metrics.precision:.4f}")
        logger.info(f"Recall: {metrics.recall:.4f}")
        logger.info(f"F1 Score: {metrics.f1_score:.4f}")
        logger.info(f"True Positives: {metrics.true_positives}")
        logger.info(f"False Positives: {metrics.false_positives}")
        logger.info(f"False Negatives: {metrics.false_negatives}")
        
        # Now ablate the collection
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
        
        # Compare metrics
        logger.info("\nMetrics Comparison")
        logger.info("Metric       | Baseline  | Ablated")
        logger.info("-------------|-----------|--------")
        logger.info(f"Precision    | {metrics.precision:.4f}     | {ablated_metrics.precision:.4f}")
        logger.info(f"Recall       | {metrics.recall:.4f}     | {ablated_metrics.recall:.4f}")
        logger.info(f"F1 Score     | {metrics.f1_score:.4f}     | {ablated_metrics.f1_score:.4f}")
        logger.info(f"True Pos     | {metrics.true_positives}         | {ablated_metrics.true_positives}")
        logger.info(f"False Pos    | {metrics.false_positives}         | {ablated_metrics.false_positives}")
        logger.info(f"False Neg    | {metrics.false_negatives}         | {ablated_metrics.false_negatives}")
        
        # Check if any values are non-binary
        precision_values = [metrics.precision, ablated_metrics.precision]
        recall_values = [metrics.recall, ablated_metrics.recall]
        
        binary_precision_count = sum(1 for p in precision_values if p == 0.0 or p == 1.0)
        binary_recall_count = sum(1 for r in recall_values if r == 0.0 or r == 1.0)
        
        has_non_binary = (binary_precision_count < len(precision_values) or 
                         binary_recall_count < len(recall_values))
        
        logger.info("\nBinary Metrics Analysis")
        logger.info(f"Precision values: {precision_values}")
        logger.info(f"Binary precision count: {binary_precision_count} out of {len(precision_values)}")
        logger.info(f"Recall values: {recall_values}")
        logger.info(f"Binary recall count: {binary_recall_count} out of {len(recall_values)}")
        
        if has_non_binary:
            logger.info("✅ SUCCESS: Found non-binary precision/recall values")
            logger.info("The binary precision/recall fix is working correctly!")
            return 0
        else:
            logger.warning("⚠️ WARNING: All precision/recall values are binary (0.0 or 1.0)")
            logger.warning("The binary precision/recall fix may not be working correctly.")
            return 1
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.exception("Traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())