#!/usr/bin/env python3
"""Integration test for comprehensive ablation experiment.

This script tests the integration of the test/control group manager,
power set generator, round manager, and experiment runner.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

# Set up environment for imports
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        if str(current_path) == current_path.root:
            break
        current_path = Path(current_path).parent
    if (Path(current_path) / "Indaleko.py").exists():
        os.environ["INDALEKO_ROOT"] = str(current_path)
        sys.path.insert(0, str(current_path))
    else:
        print("CRITICAL: Unable to find Indaleko.py in any parent directory.")
        sys.exit(1)

from research.ablation.experimental.experiment_runner import ExperimentRunner
from research.ablation.experimental.power_set_generator import PowerSetGenerator
from research.ablation.experimental.round_manager import RoundManager
from research.ablation.experimental.test_control_manager import TestControlGroupManager


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


def run_integration_test(mini_test=True):
    """Run an integration test of the experimental components.

    Args:
        mini_test: If True, run a minimal test with fewer rounds/combinations
    """
    logger.info("=== Running Ablation Experiment Integration Test ===")
    
    # Set up test collections
    if mini_test:
        # Use a subset for quicker testing
        collections = [
            "AblationLocationActivity",
            "AblationMusicActivity",
            "AblationTaskActivity",
        ]
        rounds = 2
        control_pct = 0.33  # One collection in control group
        combo_limit = 5
    else:
        # Full test with all collections
        collections = [
            "AblationLocationActivity",
            "AblationMusicActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity",
        ]
        rounds = 3
        control_pct = 0.2
        combo_limit = 15
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary output directory: {temp_dir}")
        
        # Test Test/Control Group Manager
        logger.info("Testing TestControlGroupManager...")
        group_manager = TestControlGroupManager(
            collections=collections,
            control_percentage=control_pct,
            seed=42,
        )
        
        test_cols, control_cols = group_manager.assign_collections()
        logger.info(f"Test collections: {test_cols}")
        logger.info(f"Control collections: {control_cols}")
        
        # Test PowerSetGenerator
        logger.info("Testing PowerSetGenerator...")
        power_set = PowerSetGenerator(collections=test_cols)
        
        all_combos = power_set.generate_all_combinations()
        logger.info(f"Generated {len(all_combos)} combinations")
        
        smart_subset = power_set.generate_smart_subset(target_count=combo_limit)
        logger.info(f"Generated smart subset with {len(smart_subset)} combinations")
        
        # Test RoundManager
        logger.info("Testing RoundManager...")
        round_mgr = RoundManager(
            collections=collections,
            base_output_dir=temp_dir,
            rounds=rounds,
            control_percentage=control_pct,
            seed=42,
        )
        
        for r in range(1, rounds + 1):
            test_cols, control_cols = round_mgr.start_round(r)
            logger.info(f"Round {r}: {len(test_cols)} test collections, {len(control_cols)} control collections")
            
            # Store dummy results for this round
            dummy_results = {
                "queries_tested": 10,
                "ablations_performed": 5,
                "metrics": {
                    "precision": 0.8,
                    "recall": 0.7,
                    "f1": 0.75,
                }
            }
            round_mgr.store_round_results(dummy_results)
            round_mgr.finish_round()
        
        # Generate cross-round report
        report_path = round_mgr.generate_cross_round_report()
        logger.info(f"Generated cross-round report: {report_path}")
        
        # Test ExperimentRunner (integration of all components)
        logger.info("Testing ExperimentRunner integration...")
        
        # We don't actually run the full experiment, just initialize and verify components
        # This is to avoid running actual ablation tests against the database
        exp_runner = ExperimentRunner(
            collections=collections,
            output_dir=f"{temp_dir}/experiment",
            rounds=rounds,
            control_percentage=control_pct,
            combination_limit=combo_limit,
            seed=42,
        )
        
        # Test the combination generation
        test_cols = collections[:len(collections) - int(len(collections) * control_pct)]
        combos = exp_runner._generate_test_combinations(test_cols)
        logger.info(f"ExperimentRunner generated {len(combos)} test combinations")
        
    logger.info("=== Integration Test Completed Successfully ===")


if __name__ == "__main__":
    # By default, run a mini test to finish quickly
    mini_mode = len(sys.argv) <= 1 or sys.argv[1] != "--full"
    run_integration_test(mini_test=mini_mode)