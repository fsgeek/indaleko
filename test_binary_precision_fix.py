#!/usr/bin/env python3
"""
Test script to verify that our fixes to the binary precision/recall issue work correctly.
This script runs specific test cases to ensure that precision and recall values span a
range of values, not just 0.0 and 1.0.

Project Indaleko
Copyright (C) 2024-2025 Tony Mason
"""

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from research.ablation.ablation_tester import AblationTester
from research.ablation.run_comprehensive_ablation import setup_logging


def test_binary_precision_fix():
    """
    Test that the fixes to the binary precision/recall issue work correctly.
    This function tests various scenarios to ensure that precision and recall values
    can span a range of values, not just 0.0 and 1.0.
    """
    logger = logging.getLogger(__name__)
    logger.info("Testing binary precision/recall fix")

    # Create an ablation tester instance
    tester = AblationTester()

    # Get the available collections
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

    if not available_collections:
        logger.error("No ablation collections found, cannot proceed with test")
        return False

    # Use the first available collection for testing
    test_collection = available_collections[0]
    logger.info(f"Using collection {test_collection} for testing")

    # Generate a query ID and query text appropriate for the collection type
    query_id = uuid.uuid4()
    query_text = f"Find items in {test_collection}"

    if "Music" in test_collection:
        query_text = "Find songs by Taylor Swift"
    elif "Location" in test_collection:
        query_text = "Find activities at Home"
    elif "Task" in test_collection:
        query_text = "Find tasks related to Quarterly Report"
    elif "Collaboration" in test_collection:
        query_text = "Find meetings about Project Status"

    logger.info(f"Query ID: {query_id}")
    logger.info(f"Query text: '{query_text}'")

    # Get some entities from the collection
    cursor = tester.db.aql.execute(
        f"""
        FOR doc IN {test_collection}
        LIMIT 10
        RETURN doc._key
        """
    )

    entity_keys = list(cursor)
    entity_count = len(entity_keys)
    logger.info(f"Found {entity_count} entities in {test_collection}")

    # If we don't have enough entities, log a warning but continue with what we have
    if entity_count < 10:
        logger.warning(f"Only found {entity_count} entities, test may not produce varied precision/recall values")

    # Run tests with different subsets of entities to get varied precision/recall values
    test_results = []

    # Create a subdirectory to save our test results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"binary_precision_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    # Create different truth data sets for testing
    if entity_count >= 10:
        # Test with all entities as truth data
        truth_set_all = entity_keys

        # Test with half of the entities as truth data
        truth_set_half = entity_keys[:len(entity_keys) // 2]

        # Test with 1/4 of the entities as truth data
        truth_set_quarter = entity_keys[:len(entity_keys) // 4]

        # Test with empty truth data set
        truth_set_empty = []

        truth_sets = [
            {"name": "all", "data": truth_set_all},
            {"name": "half", "data": truth_set_half},
            {"name": "quarter", "data": truth_set_quarter},
            {"name": "empty", "data": truth_set_empty}
        ]
    else:
        # If we have few entities, just use what we have
        truth_sets = [
            {"name": "all", "data": entity_keys},
            {"name": "empty", "data": []}
        ]

    logger.info(f"Testing with {len(truth_sets)} different truth data sets")

    for truth_set in truth_sets:
        set_name = truth_set["name"]
        truth_data = truth_set["data"]

        logger.info(f"Testing truth set '{set_name}' with {len(truth_data)} entities")

        # Store the truth data
        tester.store_truth_data(query_id, test_collection, truth_data)

        # Execute the query
        results, execution_time, aql_query = tester.execute_query(
            query_id, query_text, test_collection, 100, []
        )

        # Calculate metrics
        metrics = tester.calculate_metrics(query_id, results, test_collection)

        # Log the metrics
        logger.info(f"Baseline metrics for '{set_name}' truth set:")
        logger.info(f"  Precision: {metrics.precision:.4f}")
        logger.info(f"  Recall: {metrics.recall:.4f}")
        logger.info(f"  F1 Score: {metrics.f1_score:.4f}")
        logger.info(f"  True positives: {metrics.true_positives}")
        logger.info(f"  False positives: {metrics.false_positives}")
        logger.info(f"  False negatives: {metrics.false_negatives}")

        # Now ablate the collection and run the same test
        tester.ablate_collection(test_collection)

        # Execute the query on the ablated collection
        ablated_results, ablated_time, ablated_query = tester.execute_query(
            query_id, query_text, test_collection, 100, []
        )

        # Calculate metrics
        ablated_metrics = tester.calculate_metrics(query_id, ablated_results, test_collection)

        # Log the metrics for the ablated collection
        logger.info(f"Ablated metrics for '{set_name}' truth set:")
        logger.info(f"  Precision: {ablated_metrics.precision:.4f}")
        logger.info(f"  Recall: {ablated_metrics.recall:.4f}")
        logger.info(f"  F1 Score: {ablated_metrics.f1_score:.4f}")
        logger.info(f"  True positives: {ablated_metrics.true_positives}")
        logger.info(f"  False positives: {ablated_metrics.false_positives}")
        logger.info(f"  False negatives: {ablated_metrics.false_negatives}")

        # Restore the collection
        tester.restore_collection(test_collection)

        # Store the test results
        test_results.append({
            "truth_set": set_name,
            "truth_count": len(truth_data),
            "baseline": {
                "results": len(results),
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "true_positives": metrics.true_positives,
                "false_positives": metrics.false_positives,
                "false_negatives": metrics.false_negatives
            },
            "ablated": {
                "results": len(ablated_results),
                "precision": ablated_metrics.precision,
                "recall": ablated_metrics.recall,
                "f1_score": ablated_metrics.f1_score,
                "true_positives": ablated_metrics.true_positives,
                "false_positives": ablated_metrics.false_positives,
                "false_negatives": ablated_metrics.false_negatives
            }
        })

    # Analyze the test results
    precision_values = []
    recall_values = []

    for result in test_results:
        # Include both baseline and ablated values
        precision_values.append(result["baseline"]["precision"])
        precision_values.append(result["ablated"]["precision"])
        recall_values.append(result["baseline"]["recall"])
        recall_values.append(result["ablated"]["recall"])

    # Count binary vs. non-binary values
    binary_precision_count = sum(1 for p in precision_values if p == 0.0 or p == 1.0)
    binary_recall_count = sum(1 for r in recall_values if r == 0.0 or r == 1.0)

    binary_precision_pct = binary_precision_count / len(precision_values) * 100 if precision_values else 0
    binary_recall_pct = binary_recall_count / len(recall_values) * 100 if recall_values else 0

    logger.info("\nTest Results Analysis:")
    logger.info(f"Total precision values: {len(precision_values)}")
    logger.info(f"Binary precision values (0.0 or 1.0): {binary_precision_count} ({binary_precision_pct:.1f}%)")
    logger.info(f"Non-binary precision values: {len(precision_values) - binary_precision_count} ({100 - binary_precision_pct:.1f}%)")

    logger.info(f"\nTotal recall values: {len(recall_values)}")
    logger.info(f"Binary recall values (0.0 or 1.0): {binary_recall_count} ({binary_recall_pct:.1f}%)")
    logger.info(f"Non-binary recall values: {len(recall_values) - binary_recall_count} ({100 - binary_recall_pct:.1f}%)")

    # Generate a report
    report_path = os.path.join(output_dir, "binary_precision_test_report.md")
    with open(report_path, "w") as f:
        f.write("# Binary Precision/Recall Fix Test Report\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Test collection: {test_collection}\n")
        f.write(f"Query: '{query_text}'\n\n")

        f.write("## Test Results\n\n")
        f.write("| Truth Set | Truth Count | Baseline |  |  | Ablated |  |  |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        f.write("| | | Precision | Recall | F1 | Precision | Recall | F1 |\n")

        for result in test_results:
            f.write(f"| {result['truth_set']} | {result['truth_count']} | ")
            f.write(f"{result['baseline']['precision']:.4f} | {result['baseline']['recall']:.4f} | {result['baseline']['f1_score']:.4f} | ")
            f.write(f"{result['ablated']['precision']:.4f} | {result['ablated']['recall']:.4f} | {result['ablated']['f1_score']:.4f} |\n")

        f.write("\n## Analysis\n\n")
        f.write("### Precision Values\n\n")
        f.write(f"- Total values: {len(precision_values)}\n")
        f.write(f"- Binary values (0.0 or 1.0): {binary_precision_count} ({binary_precision_pct:.1f}%)\n")
        f.write(f"- Non-binary values: {len(precision_values) - binary_precision_count} ({100 - binary_precision_pct:.1f}%)\n\n")

        f.write("### Recall Values\n\n")
        f.write(f"- Total values: {len(recall_values)}\n")
        f.write(f"- Binary values (0.0 or 1.0): {binary_recall_count} ({binary_recall_pct:.1f}%)\n")
        f.write(f"- Non-binary values: {len(recall_values) - binary_recall_count} ({100 - binary_recall_pct:.1f}%)\n\n")

        f.write("## Conclusion\n\n")
        if binary_precision_pct < 80 and binary_recall_pct < 80:
            f.write("✅ **SUCCESS**: The fixes appear to be working correctly. Precision and recall values span a range of values, not just 0.0 and 1.0.\n")
        else:
            f.write("⚠️ **WARNING**: The fixes may not be fully effective. More than 80% of precision or recall values are still binary (0.0 or 1.0).\n")

    logger.info(f"Test report written to {report_path}")

    # Return success if less than 80% of values are binary
    return binary_precision_pct < 80 and binary_recall_pct < 80


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test binary precision/recall fix")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("Testing binary precision/recall fix")

    # Run the test
    if test_binary_precision_fix():
        logger.info("✅ Binary precision/recall fix test PASSED")
        return 0
    else:
        logger.error("❌ Binary precision/recall fix test FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
