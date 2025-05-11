#!/usr/bin/env python3
"""Analyze ablation test results to verify fixes for binary precision/recall issue.

This script analyzes the results of ablation tests to ensure that the precision/recall
values span a range of values, rather than only being 0.0 or 1.0 (binary).
It processes the impact_metrics.json file from ablation test output and generates
distributions of precision, recall, and F1 scores to verify the effectiveness
of the fixes made to the ablation framework.
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def analyze_round_results(results_file):
    """Analyze a single round's results."""
    logger.info(f"Analyzing round results file: {results_file}")

    with open(results_file, 'r') as f:
        data = json.load(f)

    # Basic statistics
    round_num = data.get('round', 'unknown')
    test_collections = data.get('test_collections', [])
    control_collections = data.get('control_collections', [])

    logger.info(f"Round: {round_num}")
    logger.info(f"Test collections: {', '.join(test_collections)}")
    logger.info(f"Control collections: {', '.join(control_collections)}")

    # Count metrics
    total_metrics = 0
    non_zero_f1 = 0
    non_zero_collections = set()

    # Track min/max/avg
    f1_scores = []
    precision_scores = []
    recall_scores = []

    # Track binary vs. non-binary values
    binary_precision = 0
    binary_recall = 0
    binary_f1 = 0

    impact_metrics = data.get('results', {}).get('impact_metrics', {})
    for collection, impacts in impact_metrics.items():
        for query_id, results in impacts.items():
            for result_key, result in results.items():
                if isinstance(result, dict) and 'f1_score' in result:
                    total_metrics += 1
                    f1_score = result.get('f1_score', 0)
                    precision = result.get('precision', 0)
                    recall = result.get('recall', 0)

                    f1_scores.append(f1_score)
                    precision_scores.append(precision)
                    recall_scores.append(recall)

                    # Count binary values (0.0 or 1.0)
                    if precision == 0.0 or precision == 1.0:
                        binary_precision += 1
                    if recall == 0.0 or recall == 1.0:
                        binary_recall += 1
                    if f1_score == 0.0 or f1_score == 1.0:
                        binary_f1 += 1

                    if f1_score > 0:
                        non_zero_f1 += 1
                        non_zero_collections.add(collection)

    logger.info(f"Total metrics with F1 scores: {total_metrics}")
    logger.info(f"Non-zero F1 scores: {non_zero_f1} ({(non_zero_f1/total_metrics)*100:.2f}% if {total_metrics} > 0 else 0)")

    # Report distribution of values
    if f1_scores:
        logger.info(f"F1 score range: {min(f1_scores):.4f} - {max(f1_scores):.4f}")
        logger.info(f"Average F1 score: {sum(f1_scores)/len(f1_scores):.4f}")
        logger.info(f"Binary F1 scores (0.0 or 1.0): {binary_f1}/{len(f1_scores)} ({binary_f1/len(f1_scores)*100:.2f}%)")

    if precision_scores:
        logger.info(f"Precision range: {min(precision_scores):.4f} - {max(precision_scores):.4f}")
        logger.info(f"Average precision: {sum(precision_scores)/len(precision_scores):.4f}")
        logger.info(f"Binary precision values (0.0 or 1.0): {binary_precision}/{len(precision_scores)} ({binary_precision/len(precision_scores)*100:.2f}%)")

    if recall_scores:
        logger.info(f"Recall range: {min(recall_scores):.4f} - {max(recall_scores):.4f}")
        logger.info(f"Average recall: {sum(recall_scores)/len(recall_scores):.4f}")
        logger.info(f"Binary recall values (0.0 or 1.0): {binary_recall}/{len(recall_scores)} ({binary_recall/len(recall_scores)*100:.2f}%)")

    if non_zero_collections:
        logger.info(f"Collections with non-zero F1 scores: {', '.join(non_zero_collections)}")

    return {
        "total_metrics": total_metrics,
        "f1_scores": f1_scores,
        "precision_scores": precision_scores,
        "recall_scores": recall_scores,
        "binary_precision": binary_precision,
        "binary_recall": binary_recall,
        "binary_f1": binary_f1
    }


def analyze_impact_metrics(metrics_file, output_dir=None):
    """Analyze impact metrics to verify precision/recall distribution.

    Args:
        metrics_file: Path to the impact_metrics.json file.
        output_dir: Directory to save visualizations. If None, use directory containing metrics_file.

    Returns:
        dict: Analysis results.
    """
    logger.info(f"Analyzing metrics file: {metrics_file}")

    # Determine output directory
    if not output_dir:
        output_dir = os.path.dirname(metrics_file)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load the metrics file
    try:
        with open(metrics_file, 'r') as f:
            impact_metrics = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metrics file: {e}")
        return None

    # Extract all precision, recall, and F1 values
    precision_values = []
    recall_values = []
    f1_values = []

    # Store values by collection for per-collection analysis
    collection_metrics = defaultdict(lambda: {"precision": [], "recall": [], "f1": []})

    # Track truth data sizes
    truth_data_sizes = []
    result_sizes = []
    true_positives = []
    false_positives = []
    false_negatives = []

    # Track results by ablation status
    ablated_metrics = {"precision": [], "recall": [], "f1": []}
    non_ablated_metrics = {"precision": [], "recall": [], "f1": []}

    # Extract values from all queries
    for query_id, query_data in impact_metrics.items():
        results = query_data.get("results", {})
        for impact_key, metrics in results.items():
            # Extract collection names
            if "_impact_on_" in impact_key:
                src, dst = impact_key.split("_impact_on_")
                src = src.split("Ablation")[1].split("Activity")[0] if "Ablation" in src else src
                dst = dst.split("Ablation")[1].split("Activity")[0] if "Ablation" in dst else dst

                # Get metrics values
                precision = metrics.get("precision", None)
                recall = metrics.get("recall", None)
                f1_score = metrics.get("f1_score", None)

                if precision is not None and recall is not None and f1_score is not None:
                    precision_values.append(precision)
                    recall_values.append(recall)
                    f1_values.append(f1_score)

                    # Store by collection
                    collection_metrics[src]["precision"].append(precision)
                    collection_metrics[src]["recall"].append(recall)
                    collection_metrics[src]["f1"].append(f1_score)

                    # Store counts for analyzing distribution
                    if "truth_data_count" in metrics:
                        truth_data_sizes.append(metrics.get("truth_data_count", 0))
                    if "result_count" in metrics:
                        result_sizes.append(metrics.get("result_count", 0))
                    if "true_positives" in metrics:
                        true_positives.append(metrics.get("true_positives", 0))
                    if "false_positives" in metrics:
                        false_positives.append(metrics.get("false_positives", 0))
                    if "false_negatives" in metrics:
                        false_negatives.append(metrics.get("false_negatives", 0))

                    # Check if this was an ablated collection
                    metadata = metrics.get("metadata", {})
                    if "ablated_collection" in metadata:
                        # This is a measurement of an ablated collection's impact
                        ablated_metrics["precision"].append(precision)
                        ablated_metrics["recall"].append(recall)
                        ablated_metrics["f1"].append(f1_score)
                    else:
                        # This is a baseline measurement
                        non_ablated_metrics["precision"].append(precision)
                        non_ablated_metrics["recall"].append(recall)
                        non_ablated_metrics["f1"].append(f1_score)

    # Analyze distribution of values
    analysis = {}

    # Overall metrics
    if precision_values:
        analysis["precision"] = {
            "min": min(precision_values),
            "max": max(precision_values),
            "mean": np.mean(precision_values),
            "median": np.median(precision_values),
            "std": np.std(precision_values),
            "unique_values": len(set(precision_values)),
            "binary_percentage": percentage_binary(precision_values)
        }

    if recall_values:
        analysis["recall"] = {
            "min": min(recall_values),
            "max": max(recall_values),
            "mean": np.mean(recall_values),
            "median": np.median(recall_values),
            "std": np.std(recall_values),
            "unique_values": len(set(recall_values)),
            "binary_percentage": percentage_binary(recall_values)
        }

    if f1_values:
        analysis["f1"] = {
            "min": min(f1_values),
            "max": max(f1_values),
            "mean": np.mean(f1_values),
            "median": np.median(f1_values),
            "std": np.std(f1_values),
            "unique_values": len(set(f1_values)),
            "binary_percentage": percentage_binary(f1_values)
        }

    # Analysis by collection
    analysis["collections"] = {}
    for collection, metrics in collection_metrics.items():
        if metrics["precision"]:
            analysis["collections"][collection] = {
                "precision": {
                    "min": min(metrics["precision"]),
                    "max": max(metrics["precision"]),
                    "mean": np.mean(metrics["precision"]),
                    "unique_values": len(set(metrics["precision"])),
                    "binary_percentage": percentage_binary(metrics["precision"])
                },
                "recall": {
                    "min": min(metrics["recall"]),
                    "max": max(metrics["recall"]),
                    "mean": np.mean(metrics["recall"]),
                    "unique_values": len(set(metrics["recall"])),
                    "binary_percentage": percentage_binary(metrics["recall"])
                },
                "f1": {
                    "min": min(metrics["f1"]),
                    "max": max(metrics["f1"]),
                    "mean": np.mean(metrics["f1"]),
                    "unique_values": len(set(metrics["f1"])),
                    "binary_percentage": percentage_binary(metrics["f1"])
                }
            }

    # Analysis by ablation status
    if ablated_metrics["precision"]:
        analysis["ablated"] = {
            "precision": {
                "min": min(ablated_metrics["precision"]),
                "max": max(ablated_metrics["precision"]),
                "mean": np.mean(ablated_metrics["precision"]),
                "unique_values": len(set(ablated_metrics["precision"])),
                "binary_percentage": percentage_binary(ablated_metrics["precision"])
            },
            "recall": {
                "min": min(ablated_metrics["recall"]),
                "max": max(ablated_metrics["recall"]),
                "mean": np.mean(ablated_metrics["recall"]),
                "unique_values": len(set(ablated_metrics["recall"])),
                "binary_percentage": percentage_binary(ablated_metrics["recall"])
            },
            "f1": {
                "min": min(ablated_metrics["f1"]),
                "max": max(ablated_metrics["f1"]),
                "mean": np.mean(ablated_metrics["f1"]),
                "unique_values": len(set(ablated_metrics["f1"])),
                "binary_percentage": percentage_binary(ablated_metrics["f1"])
            }
        }

    if non_ablated_metrics["precision"]:
        analysis["non_ablated"] = {
            "precision": {
                "min": min(non_ablated_metrics["precision"]),
                "max": max(non_ablated_metrics["precision"]),
                "mean": np.mean(non_ablated_metrics["precision"]),
                "unique_values": len(set(non_ablated_metrics["precision"])),
                "binary_percentage": percentage_binary(non_ablated_metrics["precision"])
            },
            "recall": {
                "min": min(non_ablated_metrics["recall"]),
                "max": max(non_ablated_metrics["recall"]),
                "mean": np.mean(non_ablated_metrics["recall"]),
                "unique_values": len(set(non_ablated_metrics["recall"])),
                "binary_percentage": percentage_binary(non_ablated_metrics["recall"])
            },
            "f1": {
                "min": min(non_ablated_metrics["f1"]),
                "max": max(non_ablated_metrics["f1"]),
                "mean": np.mean(non_ablated_metrics["f1"]),
                "unique_values": len(set(non_ablated_metrics["f1"])),
                "binary_percentage": percentage_binary(non_ablated_metrics["f1"])
            }
        }

    # Generate visualizations
    if precision_values:
        # Distribution of precision values
        plt.figure(figsize=(10, 6))
        plt.hist(precision_values, bins=20, alpha=0.7, color='blue')
        plt.title('Distribution of Precision Values')
        plt.xlabel('Precision')
        plt.ylabel('Frequency')
        plt.grid(alpha=0.3)
        plt.savefig(os.path.join(output_dir, 'precision_distribution.png'))
        plt.close()

        # Distribution of recall values
        plt.figure(figsize=(10, 6))
        plt.hist(recall_values, bins=20, alpha=0.7, color='green')
        plt.title('Distribution of Recall Values')
        plt.xlabel('Recall')
        plt.ylabel('Frequency')
        plt.grid(alpha=0.3)
        plt.savefig(os.path.join(output_dir, 'recall_distribution.png'))
        plt.close()

        # Distribution of F1 scores
        plt.figure(figsize=(10, 6))
        plt.hist(f1_values, bins=20, alpha=0.7, color='red')
        plt.title('Distribution of F1 Scores')
        plt.xlabel('F1 Score')
        plt.ylabel('Frequency')
        plt.grid(alpha=0.3)
        plt.savefig(os.path.join(output_dir, 'f1_distribution.png'))
        plt.close()

        # Precision vs. Recall scatter plot
        plt.figure(figsize=(10, 6))
        plt.scatter(precision_values, recall_values, alpha=0.7)
        plt.title('Precision vs. Recall')
        plt.xlabel('Precision')
        plt.ylabel('Recall')
        plt.grid(alpha=0.3)
        plt.xlim(-0.05, 1.05)
        plt.ylim(-0.05, 1.05)
        plt.savefig(os.path.join(output_dir, 'precision_recall_scatter.png'))
        plt.close()

        # Compare distributions for ablated vs non-ablated (if both exist)
        if ablated_metrics["precision"] and non_ablated_metrics["precision"]:
            # Precision comparison
            plt.figure(figsize=(10, 6))
            plt.hist([ablated_metrics["precision"], non_ablated_metrics["precision"]],
                    bins=20, alpha=0.7, label=['Ablated', 'Non-Ablated'])
            plt.title('Precision: Ablated vs. Non-Ablated')
            plt.xlabel('Precision')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.savefig(os.path.join(output_dir, 'precision_ablation_comparison.png'))
            plt.close()

            # Recall comparison
            plt.figure(figsize=(10, 6))
            plt.hist([ablated_metrics["recall"], non_ablated_metrics["recall"]],
                    bins=20, alpha=0.7, label=['Ablated', 'Non-Ablated'])
            plt.title('Recall: Ablated vs. Non-Ablated')
            plt.xlabel('Recall')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.savefig(os.path.join(output_dir, 'recall_ablation_comparison.png'))
            plt.close()

            # F1 comparison
            plt.figure(figsize=(10, 6))
            plt.hist([ablated_metrics["f1"], non_ablated_metrics["f1"]],
                    bins=20, alpha=0.7, label=['Ablated', 'Non-Ablated'])
            plt.title('F1 Score: Ablated vs. Non-Ablated')
            plt.xlabel('F1 Score')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(alpha=0.3)
            plt.savefig(os.path.join(output_dir, 'f1_ablation_comparison.png'))
            plt.close()

    # Generate the analysis report
    report_path = os.path.join(output_dir, 'metrics_analysis.md')
    with open(report_path, 'w') as f:
        f.write('# Ablation Metrics Analysis Report\n\n')

        f.write('## Overview\n\n')
        f.write(f'Total queries analyzed: {len(impact_metrics)}\n')
        f.write(f'Total metric points: {len(precision_values)}\n')
        f.write(f'Collections analyzed: {len(collection_metrics)}\n\n')

        f.write('## Binary Precision/Recall Analysis\n\n')
        f.write('This analysis checks if the precision and recall values are distributed across the range (0.0 to 1.0) ')
        f.write('or are mostly binary (0.0 or 1.0).\n\n')

        f.write('### Overall Metrics\n\n')
        f.write('| Metric | Min | Max | Mean | Median | Std Dev | Unique Values | Binary % |\n')
        f.write('|--------|-----|-----|------|--------|---------|---------------|----------|\n')

        if "precision" in analysis:
            p = analysis["precision"]
            f.write(f'| Precision | {p["min"]:.3f} | {p["max"]:.3f} | {p["mean"]:.3f} | {p["median"]:.3f} | {p["std"]:.3f} | {p["unique_values"]} | {p["binary_percentage"]:.1f}% |\n')

        if "recall" in analysis:
            r = analysis["recall"]
            f.write(f'| Recall | {r["min"]:.3f} | {r["max"]:.3f} | {r["mean"]:.3f} | {r["median"]:.3f} | {r["std"]:.3f} | {r["unique_values"]} | {r["binary_percentage"]:.1f}% |\n')

        if "f1" in analysis:
            f1 = analysis["f1"]
            f.write(f'| F1 Score | {f1["min"]:.3f} | {f1["max"]:.3f} | {f1["mean"]:.3f} | {f1["median"]:.3f} | {f1["std"]:.3f} | {f1["unique_values"]} | {f1["binary_percentage"]:.1f}% |\n')

        f.write('\n')

        # Interpretation of results
        binary_threshold = 80.0  # If more than 80% of values are binary (0.0 or 1.0), we have a problem
        has_binary_issue = False

        if "precision" in analysis and analysis["precision"]["binary_percentage"] > binary_threshold:
            has_binary_issue = True
        if "recall" in analysis and analysis["recall"]["binary_percentage"] > binary_threshold:
            has_binary_issue = True

        f.write('### Interpretation\n\n')
        if has_binary_issue:
            f.write('**⚠️ ISSUE DETECTED**: The metrics still show a high percentage of binary values (0.0 or 1.0). ')
            f.write('This suggests that the ablation framework modifications have not completely resolved the binary precision/recall issue. ')
            f.write('Further investigation is needed to ensure that precision and recall span the full range of values.\n\n')
        else:
            f.write('**✅ FIXES EFFECTIVE**: The metrics show a good distribution of values beyond binary. ')
            f.write('This suggests that the ablation framework modifications have successfully addressed the binary precision/recall issue. ')
            f.write('The framework now appears to be capturing the nuanced impact of ablating collections on search quality.\n\n')

        # Collection-specific analysis
        f.write('## Collection-Specific Analysis\n\n')
        f.write('### Precision Metrics by Collection\n\n')
        f.write('| Collection | Min | Max | Mean | Unique Values | Binary % |\n')
        f.write('|------------|-----|-----|------|---------------|----------|\n')

        for collection, metrics in sorted(analysis.get("collections", {}).items()):
            p = metrics["precision"]
            f.write(f'| {collection} | {p["min"]:.3f} | {p["max"]:.3f} | {p["mean"]:.3f} | {p["unique_values"]} | {p["binary_percentage"]:.1f}% |\n')

        f.write('\n')

        # Ablation status analysis
        f.write('## Ablation Status Comparison\n\n')

        if "ablated" in analysis and "non_ablated" in analysis:
            f.write('### Precision\n\n')
            f.write('| Status | Min | Max | Mean | Unique Values | Binary % |\n')
            f.write('|--------|-----|-----|------|---------------|----------|\n')

            ablated_p = analysis["ablated"]["precision"]
            non_ablated_p = analysis["non_ablated"]["precision"]

            f.write(f'| Ablated | {ablated_p["min"]:.3f} | {ablated_p["max"]:.3f} | {ablated_p["mean"]:.3f} | {ablated_p["unique_values"]} | {ablated_p["binary_percentage"]:.1f}% |\n')
            f.write(f'| Non-Ablated | {non_ablated_p["min"]:.3f} | {non_ablated_p["max"]:.3f} | {non_ablated_p["mean"]:.3f} | {non_ablated_p["unique_values"]} | {non_ablated_p["binary_percentage"]:.1f}% |\n')

            f.write('\n### Recall\n\n')
            f.write('| Status | Min | Max | Mean | Unique Values | Binary % |\n')
            f.write('|--------|-----|-----|------|---------------|----------|\n')

            ablated_r = analysis["ablated"]["recall"]
            non_ablated_r = analysis["non_ablated"]["recall"]

            f.write(f'| Ablated | {ablated_r["min"]:.3f} | {ablated_r["max"]:.3f} | {ablated_r["mean"]:.3f} | {ablated_r["unique_values"]} | {ablated_r["binary_percentage"]:.1f}% |\n')
            f.write(f'| Non-Ablated | {non_ablated_r["min"]:.3f} | {non_ablated_r["max"]:.3f} | {non_ablated_r["mean"]:.3f} | {non_ablated_r["unique_values"]} | {non_ablated_r["binary_percentage"]:.1f}% |\n')

            f.write('\n### F1 Score\n\n')
            f.write('| Status | Min | Max | Mean | Unique Values | Binary % |\n')
            f.write('|--------|-----|-----|------|---------------|----------|\n')

            ablated_f1 = analysis["ablated"]["f1"]
            non_ablated_f1 = analysis["non_ablated"]["f1"]

            f.write(f'| Ablated | {ablated_f1["min"]:.3f} | {ablated_f1["max"]:.3f} | {ablated_f1["mean"]:.3f} | {ablated_f1["unique_values"]} | {ablated_f1["binary_percentage"]:.1f}% |\n')
            f.write(f'| Non-Ablated | {non_ablated_f1["min"]:.3f} | {non_ablated_f1["max"]:.3f} | {non_ablated_f1["mean"]:.3f} | {non_ablated_f1["unique_values"]} | {non_ablated_f1["binary_percentage"]:.1f}% |\n')

        # Include visualizations in the report
        f.write('\n## Visualizations\n\n')
        f.write('### Precision Distribution\n\n')
        f.write('![Precision Distribution](precision_distribution.png)\n\n')

        f.write('### Recall Distribution\n\n')
        f.write('![Recall Distribution](recall_distribution.png)\n\n')

        f.write('### F1 Score Distribution\n\n')
        f.write('![F1 Score Distribution](f1_distribution.png)\n\n')

        f.write('### Precision vs. Recall\n\n')
        f.write('![Precision vs. Recall](precision_recall_scatter.png)\n\n')

        if "ablated" in analysis and "non_ablated" in analysis:
            f.write('### Ablation Comparisons\n\n')
            f.write('![Precision Ablation Comparison](precision_ablation_comparison.png)\n\n')
            f.write('![Recall Ablation Comparison](recall_ablation_comparison.png)\n\n')
            f.write('![F1 Ablation Comparison](f1_ablation_comparison.png)\n\n')

        # Recommendations
        f.write('## Recommendations\n\n')

        if has_binary_issue:
            f.write('Based on the analysis, the following recommendations are made:\n\n')
            f.write('1. **Further investigate the query construction**: Ensure that ablated collections are still queried with appropriate filters\n')
            f.write('2. **Check truth data management**: Verify that truth data is being properly stored and retrieved\n')
            f.write('3. **Examine metrics calculation**: Review the calculation of precision and recall to ensure proper handling of edge cases\n')
            f.write('4. **Implement diagnostic logging**: Add more detailed logging of precision/recall calculation to identify issues\n')
            f.write('5. **Test with simpler cases first**: Create simplified test cases with known expected results to validate the metrics calculation\n')
        else:
            f.write('Based on the analysis, the following next steps are recommended:\n\n')
            f.write('1. **Run comprehensive ablation tests**: The framework appears to be functioning correctly; proceed with full ablation studies\n')
            f.write('2. **Monitor for any regression**: Continue to check that precision/recall values remain well-distributed\n')
            f.write('3. **Validate against known test cases**: Create test cases with known expected results to further validate the framework\n')
            f.write('4. **Document the fixes**: Update documentation to explain the changes made to fix the binary precision/recall issue\n')

    logger.info(f"Analysis report saved to {report_path}")
    return analysis


def percentage_binary(values):
    """Calculate the percentage of values that are 0.0 or 1.0."""
    if not values:
        return 0.0

    binary_count = sum(1 for v in values if v == 0.0 or v == 1.0)
    return (binary_count / len(values)) * 100.0


def analyze_results_directory(results_dir):
    """Analyze results from an ablation experiment directory."""
    logger.info(f"Analyzing results directory: {results_dir}")

    # Ensure results directory exists
    if not os.path.exists(results_dir):
        logger.error(f"Results directory not found: {results_dir}")
        return False

    # Find round directories
    round_dirs = sorted(Path(results_dir).glob("round_*"))
    if not round_dirs:
        logger.warning(f"No round directories found in {results_dir}")

        # Check if this is a simple ablation result with impact_metrics.json at the top level
        metrics_file = os.path.join(results_dir, "impact_metrics.json")
        if os.path.exists(metrics_file):
            logger.info(f"Found impact_metrics.json at top level, analyzing directly")
            analyze_impact_metrics(metrics_file, results_dir)
            return True
        else:
            logger.error(f"No impact_metrics.json found in {results_dir}")
            return False

    # Analyze each round
    for round_dir in round_dirs:
        logger.info(f"Analyzing round directory: {round_dir}")

        # Try to find impact_metrics.json in this round
        metrics_file = os.path.join(round_dir, "impact_metrics.json")
        if os.path.exists(metrics_file):
            analyze_impact_metrics(metrics_file, round_dir)

        # Also look for round_results.json
        results_file = os.path.join(round_dir, "round_results.json")
        if os.path.exists(results_file):
            analyze_round_results(results_file)

    logger.info(f"Completed analysis of results directory: {results_dir}")
    return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze ablation test results")
    parser.add_argument(
        "--input-file",
        type=str,
        help="Path to the impact_metrics.json file from ablation test output"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        help="Path to the ablation results directory (contains round_* subdirectories)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save analysis results (defaults to directory containing the input file)"
    )
    args = parser.parse_args()

    # Validate input parameters
    if not args.input_file and not args.results_dir:
        logger.error("Either --input-file or --results-dir must be provided")
        parser.print_help()
        return 1

    # If an input file is provided, analyze it directly
    if args.input_file:
        if not os.path.exists(args.input_file):
            logger.error(f"Input file not found: {args.input_file}")
            return 1

        analyze_impact_metrics(args.input_file, args.output_dir)

    # If a results directory is provided, analyze it
    if args.results_dir:
        if not os.path.exists(args.results_dir):
            logger.error(f"Results directory not found: {args.results_dir}")
            return 1

        analyze_results_directory(args.results_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
