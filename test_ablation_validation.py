#!/usr/bin/env python3
"""Test script for the ablation validation functionality.

This script tests the validation functionality added to analyze_results.py.
It creates a set of test cases with known issues and verifies that the
validation function correctly identifies all of them.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

# Import the validation function from analyze_results
try:
    from analyze_results import validate_ablation_results, analyze_impact_metrics
except ImportError:
    # Add the parent directory to the path if running from a different directory
    sys.path.append(str(Path(__file__).parent))
    from analyze_results import validate_ablation_results, analyze_impact_metrics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_test_data():
    """Create test data with known validation issues."""
    # Base template for a metric entry
    def create_base_metric(query_id, collection, ablated=False, precision=0.5, recall=0.5,
                          tp=5, fp=5, fn=5, result_count=10, truth_count=10, aql=""):
        # For test_query_4, we need both normal and ablated present for the identical queries check
        metadata = {
            "collection": collection
        }

        # Only add the ablated_collection field if this is an ablated query
        if ablated:
            metadata["ablated_collection"] = collection

        return {
            "query_id": query_id,
            "precision": precision,
            "recall": recall,
            "f1_score": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "result_count": result_count,
            "truth_data_count": truth_count,
            "aql_query": aql,
            "metadata": metadata
        }

    # Create test data with different validation issues
    test_metrics = {"impact_metrics": {}}

    # Issue 1: precision = 1.0 but no true positives
    test_metrics["impact_metrics"]["test_query_1"] = {
        "results": {
            "MusicActivity_impact_on_LocationActivity": {
                "ablation_impact": create_base_metric(
                    "test_query_1", "MusicActivity", ablated=True,
                    precision=1.0, recall=1.0, tp=0, fp=0, fn=0, result_count=0, truth_count=0,
                    aql="FOR doc IN MusicActivity FILTER doc.artist == 'Taylor Swift' RETURN doc"
                )
            }
        }
    }

    # Issue 2: f1 = 0.0 but false negatives > 0
    test_metrics["impact_metrics"]["test_query_2"] = {
        "results": {
            "LocationActivity_impact_on_TaskActivity": {
                "ablation_impact": create_base_metric(
                    "test_query_2", "LocationActivity", ablated=True,
                    precision=0.0, recall=0.0, tp=0, fp=0, fn=5, result_count=0, truth_count=5,
                    aql="FOR doc IN LocationActivity FILTER doc.city == 'San Francisco' RETURN doc"
                )
            }
        }
    }

    # Issue 3: result_count inconsistent with tp + fp
    test_metrics["impact_metrics"]["test_query_3"] = {
        "results": {
            "TaskActivity_impact_on_MusicActivity": {
                "ablation_impact": create_base_metric(
                    "test_query_3", "TaskActivity", ablated=True,
                    precision=0.5, recall=0.5, tp=5, fp=5, fn=5, result_count=15, truth_count=10,
                    aql="FOR doc IN TaskActivity FILTER doc.status == 'Complete' RETURN doc"
                )
            }
        }
    }

    # Issue 4: Identical queries for ablated and non-ablated runs
    same_query = "FOR doc IN CollaborationActivity FILTER doc.type == 'Meeting' RETURN doc"
    test_metrics["impact_metrics"]["test_query_4"] = {
        "results": {
            "CollaborationActivity_impact_on_StorageActivity": {
                "ablated": create_base_metric(  # <-- Changed to match the key used in validate_ablation_results
                    "test_query_4", "CollaborationActivity", ablated=True,
                    precision=0.4, recall=0.6, tp=4, fp=6, fn=3, result_count=10, truth_count=7,
                    aql=same_query
                ),
                "normal": create_base_metric(  # <-- Changed to match the key used in validate_ablation_results
                    "test_query_4", "CollaborationActivity", ablated=False,
                    precision=0.7, recall=0.8, tp=7, fp=3, fn=2, result_count=10, truth_count=9,
                    aql=same_query
                )
            }
        }
    }

    # No issues - valid data
    test_metrics["impact_metrics"]["test_query_5"] = {
        "results": {
            "StorageActivity_impact_on_MediaActivity": {
                "ablation_impact": create_base_metric(
                    "test_query_5", "StorageActivity", ablated=True,
                    precision=0.6, recall=0.6, tp=6, fp=4, fn=4, result_count=10, truth_count=10,
                    aql="FOR doc IN StorageActivity FILTER doc.size > 1000000 RETURN doc"
                ),
                "baseline": create_base_metric(
                    "test_query_5", "StorageActivity", ablated=False,
                    precision=0.8, recall=0.8, tp=8, fp=2, fn=2, result_count=10, truth_count=10,
                    aql="FOR doc IN StorageActivity FILTER doc.size > 1000000 AND doc.type == 'file' RETURN doc"
                )
            }
        }
    }

    return test_metrics


def test_validation_function():
    """Test that the validation function correctly identifies all issues."""
    test_data = create_test_data()

    # Debugging: Examine the structure of the collection_queries dictionary
    # that will be built inside validate_ablation_results
    collection_queries = {}
    for outer_key, inner_data in test_data["impact_metrics"].items():
        if "results" in inner_data:
            inner_data = inner_data["results"]
        for inner_key, entry in inner_data.items():
            if isinstance(entry, dict):
                for direction, metrics in entry.items():
                    if isinstance(metrics, dict):
                        collection = None
                        ablated = False
                        query_id = metrics.get("query_id", "unknown")
                        aql = metrics.get("aql_query", "")

                        metadata = metrics.get("metadata", {})
                        if metadata:
                            collection = metadata.get("collection", None)
                            ablated = "ablated_collection" in metadata

                        if collection:
                            if collection not in collection_queries:
                                collection_queries[collection] = {}
                            if query_id not in collection_queries[collection]:
                                collection_queries[collection][query_id] = {}

                            ablation_key = "ablated" if ablated else "normal"
                            collection_queries[collection][query_id][ablation_key] = aql

    logger.info(f"Collection queries structure: {collection_queries}")
    logger.info(f"CollaborationActivity queries: {collection_queries.get('CollaborationActivity', {})}")

    validation_results = validate_ablation_results(test_data)

    logger.info(f"Found {len(validation_results)} validation issues")
    for i, (query_id, issue, severity, _) in enumerate(validation_results, 1):
        logger.info(f"Issue {i}: {severity} - {query_id} - {issue}")

    # We expect 5 issues:
    # 1. Precision = 1.0 but no true positives
    # 2. Perfect metrics with no matching activity (for test_query_1)
    # 3. F1 = 0.0 but false negatives > 0
    # 4. result_count inconsistent with tp + fp
    # 5. Identical queries for ablated and non-ablated runs
    expected_issues = 5

    if len(validation_results) != expected_issues:
        logger.error(f"Expected {expected_issues} validation issues, but found {len(validation_results)}")
        for i, (query_id, issue, severity, _) in enumerate(validation_results, 1):
            logger.info(f"Issue {i}: {severity} - {query_id} - {issue}")
        return False

    # Check for specific issues
    issues_found = {
        "precision_1_no_tp": False,
        "perfect_metrics_no_activity": False,
        "f1_0_with_fn": False,
        "inconsistent_result_count": False,
        "identical_queries": False
    }

    for query_id, issue, severity, _ in validation_results:
        if "Precision = 1.0 but true positives = 0" in issue and query_id == "test_query_1":
            issues_found["precision_1_no_tp"] = True
        elif "Perfect metrics (P=1.0, R=1.0) with no matching activity" in issue and query_id == "test_query_1":
            issues_found["perfect_metrics_no_activity"] = True
        elif "F1 = 0.0 despite having" in issue and query_id == "test_query_2":
            issues_found["f1_0_with_fn"] = True
        elif "Inconsistent metrics: result_count" in issue and query_id == "test_query_3":
            issues_found["inconsistent_result_count"] = True
        elif "Identical queries for ablated and non-ablated runs" in issue and query_id == "test_query_4":
            issues_found["identical_queries"] = True

    missing_issues = [k for k, v in issues_found.items() if not v]
    if missing_issues:
        logger.error(f"Failed to detect these issues: {', '.join(missing_issues)}")
        return False

    logger.info("✅ All expected validation issues were correctly identified")
    return True


def test_report_generation():
    """Test that the reports include validation results."""
    test_data = create_test_data()

    # Create a temporary directory for the report
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a temporary metrics file
        metrics_file = os.path.join(tmpdirname, "test_metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump(test_data, f)

        # Run the analysis
        analyze_impact_metrics(metrics_file, tmpdirname)

        # Check that the report was created
        report_file = os.path.join(tmpdirname, "metrics_analysis.md")
        if not os.path.exists(report_file):
            logger.error(f"Report file {report_file} was not created")
            return False

        # Check that the report includes validation issues
        with open(report_file, 'r') as f:
            report_content = f.read()

        if "## Validation Issues Detected" not in report_content:
            logger.error("Report does not include validation issues section")
            return False

        if "| Query ID | Issue | Severity |" not in report_content:
            logger.error("Report does not include validation issues table")
            return False

        logger.info("✅ Report generation test passed")
        return True


def main():
    """Main entry point for the script."""
    logger.info("Testing ablation validation functionality")

    validation_test_result = test_validation_function()
    report_test_result = test_report_generation()

    if validation_test_result and report_test_result:
        logger.info("✅ All tests passed! The validation functionality is working correctly.")
        return 0
    else:
        logger.error("❌ Tests failed. Please check the logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
