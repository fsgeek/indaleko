#!/usr/bin/env python3
"""Analyze ablation experiment results."""

import json
import sys
import os
from pathlib import Path

def analyze_round_results(results_file):
    """Analyze a single round's results."""
    print(f"Analyzing: {results_file}")

    with open(results_file, 'r') as f:
        data = json.load(f)

    # Basic statistics
    round_num = data.get('round', 'unknown')
    test_collections = data.get('test_collections', [])
    control_collections = data.get('control_collections', [])

    print(f"Round: {round_num}")
    print(f"Test collections: {', '.join(test_collections)}")
    print(f"Control collections: {', '.join(control_collections)}")

    # Count metrics
    total_metrics = 0
    non_zero_f1 = 0
    non_zero_collections = set()

    # Track min/max/avg
    f1_scores = []
    precision_scores = []
    recall_scores = []

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

                    if f1_score > 0:
                        non_zero_f1 += 1
                        non_zero_collections.add(collection)

    print(f"Total metrics with F1 scores: {total_metrics}")
    print(f"Non-zero F1 scores: {non_zero_f1} ({(non_zero_f1/total_metrics)*100:.2f}% if {total_metrics} > 0 else 0)")

    if f1_scores:
        print(f"F1 score range: {min(f1_scores):.2f} - {max(f1_scores):.2f}")
        print(f"Average F1 score: {sum(f1_scores)/len(f1_scores):.4f}")

    if precision_scores:
        print(f"Precision range: {min(precision_scores):.2f} - {max(precision_scores):.2f}")
        print(f"Average precision: {sum(precision_scores)/len(precision_scores):.4f}")

    if recall_scores:
        print(f"Recall range: {min(recall_scores):.2f} - {max(recall_scores):.2f}")
        print(f"Average recall: {sum(recall_scores)/len(recall_scores):.4f}")

    if non_zero_collections:
        print(f"Collections with non-zero F1 scores: {', '.join(non_zero_collections)}")

    # Count perfect precision/recall pairs - these should include our empty truth data cases
    perfect_scores = 0
    perfect_info = []

    for collection, impacts in impact_metrics.items():
        for query_id, results in impacts.items():
            for result_key, result in results.items():
                if isinstance(result, dict) and 'precision' in result and 'recall' in result:
                    if result.get('precision') == 1.0 and result.get('recall') == 1.0:
                        perfect_scores += 1
                        perfect_info.append({
                            'collection': collection,
                            'impact_key': result_key,
                            'true_positives': result.get('true_positives', 0),
                            'false_positives': result.get('false_positives', 0),
                            'false_negatives': result.get('false_negatives', 0)
                        })

    print(f"\nPerfect precision/recall scores: {perfect_scores}")
    if perfect_scores > 0:
        print("Sample of measurements with perfect scores:")
        for info in perfect_info[:5]:  # Show up to 5 examples
            print(f"  Collection: {info['collection']}, Impact: {info['impact_key']}")
            print(f"    TP: {info['true_positives']}, FP: {info['false_positives']}, FN: {info['false_negatives']}")

    # Sample a few non-zero metrics for inspection
    print("\nSample of measurements:")
    found = 0
    for collection, impacts in impact_metrics.items():
        if found >= 3:
            break
        for query_id, results in impacts.items():
            if found >= 3:
                break
            for result_key, result in results.items():
                if isinstance(result, dict) and 'f1_score' in result:
                    precision = result.get('precision', 0)
                    recall = result.get('recall', 0)
                    f1 = result.get('f1_score', 0)
                    true_pos = result.get('true_positives', 0)
                    false_pos = result.get('false_positives', 0)
                    false_neg = result.get('false_negatives', 0)

                    print(f"Collection: {collection}, Impact: {result_key}")
                    print(f"  Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
                    print(f"  TP: {true_pos}, FP: {false_pos}, FN: {false_neg}")
                    found += 1
                    if found >= 3:
                        break

def main():
    """Main entry point."""
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "./ablation_results_20250510_100057"

    # Analyze each round
    for round_dir in sorted(Path(results_dir).glob("round_*")):
        results_file = round_dir / "round_results.json"
        if results_file.exists():
            print("\n" + "="*50)
            analyze_round_results(results_file)

    print("\n" + "="*50)
    print("Analysis complete")

if __name__ == "__main__":
    main()
