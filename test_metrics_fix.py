#!/usr/bin/env python3
"""Test the fix for empty truth data metrics calculation."""

import uuid
import logging
from datetime import datetime

from research.ablation.ablation_tester import AblationTester
from research.ablation.base import AblationResult

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def test_metrics_calculation():
    """Test metrics calculation with empty truth data."""
    # Create an ablation tester instance
    tester = AblationTester()
    query_id = uuid.uuid4()
    collection_name = "AblationTestCollection"

    # Create test data
    empty_truth_data = set()  # Empty truth set
    empty_results = []  # No results
    non_empty_results = [{"_key": "result1"}, {"_key": "result2"}]  # Some results

    # Test cases
    logger.info("\n\n===== TEST 1: ABLATED + EMPTY TRUTH + NO RESULTS =====")
    metrics_ablated_empty = tester._calculate_metrics_with_truth_data(
        query_id=query_id,
        results=empty_results,  # No results
        truth_data=empty_truth_data,  # Empty truth data
        collection_name=collection_name,
        is_ablated=True  # Ablated
    )

    logger.info(f"Ablated + Empty Truth + No Results:")
    logger.info(f"  Precision: {metrics_ablated_empty.precision:.4f}")
    logger.info(f"  Recall: {metrics_ablated_empty.recall:.4f}")
    logger.info(f"  F1 Score: {metrics_ablated_empty.f1_score:.4f}")

    logger.info("\n\n===== TEST 2: NON-ABLATED + EMPTY TRUTH + NO RESULTS =====")
    metrics_non_ablated_empty_no_results = tester._calculate_metrics_with_truth_data(
        query_id=query_id,
        results=empty_results,  # No results
        truth_data=empty_truth_data,  # Empty truth data
        collection_name=collection_name,
        is_ablated=False  # Not ablated
    )

    logger.info(f"Non-Ablated + Empty Truth + No Results:")
    logger.info(f"  Precision: {metrics_non_ablated_empty_no_results.precision:.4f}")
    logger.info(f"  Recall: {metrics_non_ablated_empty_no_results.recall:.4f}")
    logger.info(f"  F1 Score: {metrics_non_ablated_empty_no_results.f1_score:.4f}")

    logger.info("\n\n===== TEST 3: NON-ABLATED + EMPTY TRUTH + SOME RESULTS =====")
    metrics_non_ablated_empty_with_results = tester._calculate_metrics_with_truth_data(
        query_id=query_id,
        results=non_empty_results,  # Some results
        truth_data=empty_truth_data,  # Empty truth data
        collection_name=collection_name,
        is_ablated=False  # Not ablated
    )

    logger.info(f"Non-Ablated + Empty Truth + Some Results:")
    logger.info(f"  Precision: {metrics_non_ablated_empty_with_results.precision:.4f}")
    logger.info(f"  Recall: {metrics_non_ablated_empty_with_results.recall:.4f}")
    logger.info(f"  F1 Score: {metrics_non_ablated_empty_with_results.f1_score:.4f}")

    # Verify that the metrics are correct
    assert metrics_ablated_empty.precision == 1.0, f"Incorrect precision for ablated+empty+no_results: expected 1.0, got {metrics_ablated_empty.precision}"
    assert metrics_ablated_empty.recall == 1.0, f"Incorrect recall for ablated+empty+no_results: expected 1.0, got {metrics_ablated_empty.recall}"
    assert metrics_ablated_empty.f1_score == 1.0, f"Incorrect F1 for ablated+empty+no_results: expected 1.0, got {metrics_ablated_empty.f1_score}"

    assert metrics_non_ablated_empty_no_results.precision == 1.0, f"Incorrect precision for non_ablated+empty+no_results: expected 1.0, got {metrics_non_ablated_empty_no_results.precision}"
    assert metrics_non_ablated_empty_no_results.recall == 1.0, f"Incorrect recall for non_ablated+empty+no_results: expected 1.0, got {metrics_non_ablated_empty_no_results.recall}"
    assert metrics_non_ablated_empty_no_results.f1_score == 1.0, f"Incorrect F1 for non_ablated+empty+no_results: expected 1.0, got {metrics_non_ablated_empty_no_results.f1_score}"

    assert metrics_non_ablated_empty_with_results.precision == 0.0, f"Incorrect precision for non_ablated+empty+with_results: expected 0.0, got {metrics_non_ablated_empty_with_results.precision}"
    assert metrics_non_ablated_empty_with_results.recall == 1.0, f"Incorrect recall for non_ablated+empty+with_results: expected 1.0, got {metrics_non_ablated_empty_with_results.recall}"
    assert metrics_non_ablated_empty_with_results.f1_score == 0.0, f"Incorrect F1 for non_ablated+empty+with_results: expected 0.0, got {metrics_non_ablated_empty_with_results.f1_score}"

    logger.info("\nAll tests passed successfully! ✅")
    return True

if __name__ == "__main__":
    test_metrics_calculation()
