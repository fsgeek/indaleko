#!/usr/bin/env python3
"""Simple test to verify the metrics calculation."""

import logging
import uuid
from research.ablation.ablation_tester import AblationTester
from research.ablation.base import AblationResult

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def test_metrics_calculation():
    """Test metrics calculation with different scenarios."""
    # Create an ablation tester instance
    tester = AblationTester()
    query_id = uuid.uuid4()
    
    # Create test data
    test_cases = [
        # Case 1: Non-ablated, empty truth, no results (perfect precision/recall)
        {
            "name": "Non-ablated, empty truth, no results",
            "truth_data": set(),
            "results": [],
            "is_ablated": False,
            "expected": {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        },
        # Case 2: Non-ablated, empty truth, some results (precision=0, recall=1.0)
        {
            "name": "Non-ablated, empty truth, some results",
            "truth_data": set(),
            "results": [{"_key": "result1"}, {"_key": "result2"}],
            "is_ablated": False,
            "expected": {"precision": 0.0, "recall": 1.0, "f1": 0.0}
        },
        # Case 3: Non-ablated, non-empty truth, all results match (perfect precision/recall)
        {
            "name": "Non-ablated, all results match",
            "truth_data": {"truth1", "truth2"},
            "results": [{"_key": "truth1"}, {"_key": "truth2"}],
            "is_ablated": False,
            "expected": {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        },
        # Case 4: Non-ablated, non-empty truth, partial match (mixed precision/recall)
        {
            "name": "Non-ablated, partial match",
            "truth_data": {"truth1", "truth2", "truth3"},
            "results": [{"_key": "truth1"}, {"_key": "other1"}],
            "is_ablated": False,
            "expected": {"precision": 0.5, "recall": 0.33, "f1": 0.4}
        },
        # Case 5: Non-ablated, non-empty truth, no match (precision=0, recall=0)
        {
            "name": "Non-ablated, no match",
            "truth_data": {"truth1", "truth2"},
            "results": [{"_key": "other1"}, {"_key": "other2"}],
            "is_ablated": False,
            "expected": {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        },
        # Case 6: Ablated, empty truth (perfect precision/recall)
        {
            "name": "Ablated, empty truth",
            "truth_data": set(),
            "results": [],
            "is_ablated": True,
            "expected": {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        },
        # Case 7: Ablated, non-empty truth (precision=0, recall=0)
        {
            "name": "Ablated, non-empty truth",
            "truth_data": {"truth1", "truth2"},
            "results": [],
            "is_ablated": True,
            "expected": {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        }
    ]
    
    # Run tests and check expectations
    precision_range = []
    recall_range = []
    
    for test_case in test_cases:
        logger.info(f"\n===== Testing: {test_case['name']} =====")
        
        # Run the metrics calculation
        metrics = tester._calculate_metrics_with_truth_data(
            query_id=query_id,
            results=test_case["results"],
            truth_data=test_case["truth_data"],
            collection_name="TestCollection",
            is_ablated=test_case["is_ablated"]
        )
        
        # Log actual values
        logger.info(f"Precision: {metrics.precision:.4f}")
        logger.info(f"Recall: {metrics.recall:.4f}")
        logger.info(f"F1 Score: {metrics.f1_score:.4f}")
        
        # Check against expected values
        precision_match = round(metrics.precision, 2) == round(test_case["expected"]["precision"], 2)
        recall_match = round(metrics.recall, 2) == round(test_case["expected"]["recall"], 2)
        f1_match = round(metrics.f1_score, 2) == round(test_case["expected"]["f1"], 2)
        
        # Log result
        if precision_match and recall_match and f1_match:
            logger.info("✅ Test passed!")
        else:
            logger.info("❌ Test failed! Expected:")
            logger.info(f"  Precision: {test_case['expected']['precision']:.4f}")
            logger.info(f"  Recall: {test_case['expected']['recall']:.4f}")
            logger.info(f"  F1: {test_case['expected']['f1']:.4f}")
        
        # Track value ranges
        precision_range.append(metrics.precision)
        recall_range.append(metrics.recall)
    
    # Print summary with ranges
    logger.info("\n===== Summary =====")
    logger.info(f"Precision range: {min(precision_range):.4f} - {max(precision_range):.4f}")
    logger.info(f"Recall range: {min(recall_range):.4f} - {max(recall_range):.4f}")
    
    # Check if we have non-binary values
    non_binary_precision = [p for p in precision_range if 0.01 < p < 0.99]
    if non_binary_precision:
        logger.info("✅ Found non-binary precision values - FIX IS WORKING!")
        logger.info(f"  Non-binary precision values: {non_binary_precision}")
    else:
        logger.info("❌ All precision values are still binary (0.0 or 1.0) - FIX MAY NOT BE WORKING")
    
    return True

if __name__ == "__main__":
    test_metrics_calculation()