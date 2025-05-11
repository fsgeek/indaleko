#!/usr/bin/env python3
"""Quick test to verify the ablation metrics fix."""

import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path

from research.ablation.ablation_tester import AblationTester
from research.ablation.ablation_tester import AblationConfig

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def run_quick_test():
    """Run a quick ablation test to verify metrics calculation."""
    logger.info("Initializing ablation tester...")
    tester = AblationTester()
    
    # Define collections to ablate
    collections = [
        "AblationMusicActivity",
        "AblationLocationActivity",
        "AblationTaskActivity"
    ]
    
    # Create ablation config
    config = AblationConfig(
        collections_to_ablate=collections,
        query_limit=20,
        include_metrics=True,
        include_execution_time=True,
        verbose=True
    )
    
    # Load test queries
    from uuid import uuid4
    query_id = uuid4()
    query_text = "Show me music I listened to while working on my project last week"
    
    logger.info(f"Running quick ablation test with query: {query_text}")
    
    # Run the ablation test
    results = tester.run_ablation_test(config, query_id, query_text)
    
    # Create output directory for results
    output_dir = Path("quick_test_results")
    output_dir.mkdir(exist_ok=True)
    
    # Save results
    with open(output_dir / "ablation_results.json", "w") as f:
        # Convert results to JSON-serializable format
        serializable_results = {}
        for key, result in results.items():
            # Convert to dict and handle UUID conversion
            result_dict = result.model_dump()
            # Convert UUID to string if present
            if 'query_id' in result_dict and hasattr(result_dict['query_id'], 'hex'):
                result_dict['query_id'] = str(result_dict['query_id'])
            serializable_results[key] = result_dict

        json.dump(serializable_results, f, indent=2)
    
    # Analyze metrics from results
    precision_values = []
    recall_values = []
    f1_values = []
    
    for key, result in results.items():
        precision = result.precision
        recall = result.recall
        f1 = result.f1_score
        
        precision_values.append(precision)
        recall_values.append(recall)
        f1_values.append(f1)
        
        logger.info(f"Result {key}:")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1 Score: {f1:.4f}")
    
    # Print summary stats
    if precision_values:
        logger.info("\nSummary Statistics:")
        logger.info(f"  Precision range: {min(precision_values):.4f} - {max(precision_values):.4f}")
        logger.info(f"  Recall range: {min(recall_values):.4f} - {max(recall_values):.4f}")
        logger.info(f"  F1 Score range: {min(f1_values):.4f} - {max(f1_values):.4f}")
        
        # Check if we still have binary precision/recall
        non_binary_precision = [p for p in precision_values if 0.01 < p < 0.99]
        if non_binary_precision:
            logger.info("✅ Found non-binary precision values - FIX IS WORKING!")
            logger.info(f"  Non-binary precision values: {non_binary_precision}")
        else:
            logger.info("❌ All precision values are still binary (0.0 or 1.0) - FIX MAY NOT BE WORKING")
    
    logger.info("Quick test completed.")
    return True

if __name__ == "__main__":
    run_quick_test()