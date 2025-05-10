#!/usr/bin/env python3
"""Tests for experimental components of the ablation framework.

This script provides tests for the test/control group manager,
power set generator, and round manager components.
"""

import logging
import os
import sys
import unittest
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

from research.ablation.experimental.test_control_manager import TestControlGroupManager
from research.ablation.experimental.power_set_generator import PowerSetGenerator
from research.ablation.experimental.round_manager import RoundManager


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


class TestExperimentalComponents(unittest.TestCase):
    """Test cases for experimental components."""

    def setUp(self):
        """Set up test environment."""
        self.collections = [
            "AblationLocationActivity",
            "AblationMusicActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity",
        ]
        self.test_output_dir = "/tmp/ablation_test_output"
        os.makedirs(self.test_output_dir, exist_ok=True)

    def test_test_control_manager(self):
        """Test the TestControlGroupManager."""
        manager = TestControlGroupManager(
            collections=self.collections,
            control_percentage=0.25,
            seed=42,
        )
        
        # Test query assignment
        query_id1 = "test-query-1"
        query_id2 = "test-query-2"
        
        group1 = manager.assign_query_group(query_id1)
        group2 = manager.assign_query_group(query_id2)
        
        # Test that assignments are consistent
        self.assertEqual(group1, manager.assign_query_group(query_id1))
        self.assertEqual(group2, manager.assign_query_group(query_id2))
        
        # Test collection assignment
        test_collections, control_collections = manager.assign_collections(control_count=2)
        
        self.assertEqual(len(test_collections), 4)
        self.assertEqual(len(control_collections), 2)
        
        # Check that collections are properly segregated
        self.assertEqual(len(set(test_collections).intersection(control_collections)), 0)
        
        # Test rotation
        test_after_rotation, control_after_rotation = manager.rotate_collections(2)
        
        # Check that 2 collections moved in each direction
        original_test = set(test_collections)
        original_control = set(control_collections)
        
        new_test = set(test_after_rotation)
        new_control = set(control_after_rotation)
        
        moved_to_test = original_control - new_control
        moved_to_control = original_test - new_test
        
        self.assertEqual(len(moved_to_test), 2)
        self.assertEqual(len(moved_to_control), 2)
        
        # Test that we get proper statistics
        stats = manager.get_group_statistics()
        self.assertIn("queries", stats)
        self.assertIn("collections", stats)

    def test_power_set_generator(self):
        """Test the PowerSetGenerator."""
        generator = PowerSetGenerator(collections=self.collections)
        
        # Test generating all combinations
        all_combinations = generator.generate_all_combinations()
        
        # Should be 2^n - 1 combinations (excluding empty set)
        expected_count = 2 ** len(self.collections) - 1
        self.assertEqual(len(all_combinations), expected_count)
        
        # Test smart subset
        smart_subset = generator.generate_smart_subset(target_count=10)
        self.assertLessEqual(len(smart_subset), 10)
        
        # Test balanced subset
        balanced_subset = generator.generate_balanced_subset(combinations_per_size=2)
        expected_balanced_count = 2 * len(self.collections)
        self.assertEqual(len(balanced_subset), expected_balanced_count)
        
        # Test single collection ablations
        single_ablations = generator.get_single_collection_ablations()
        self.assertEqual(len(single_ablations), len(self.collections))
        
        # Test single collection inclusions
        single_inclusions = generator.get_single_collection_inclusions()
        self.assertEqual(len(single_inclusions), len(self.collections))

    def test_round_manager(self):
        """Test the RoundManager."""
        round_manager = RoundManager(
            collections=self.collections,
            base_output_dir=self.test_output_dir,
            rounds=3,
            control_percentage=0.2,
            seed=42,
        )
        
        # Test starting a round
        test_collections, control_collections = round_manager.start_round()
        
        # Check that first round is initialized properly
        self.assertEqual(round_manager.current_round, 1)
        self.assertIn(1, round_manager.round_output_dirs)
        
        # Test output directory 
        round_dir = round_manager.get_round_output_dir()
        self.assertTrue(os.path.exists(round_dir))
        
        # Test storing round results
        dummy_results = {
            "queries_tested": 20,
            "ablations_performed": 10,
            "metrics": {
                "precision": 0.8,
                "recall": 0.7,
                "f1": 0.75,
            }
        }
        
        round_manager.store_round_results(dummy_results)
        self.assertIn(1, round_manager.round_results)
        
        # Test finishing round
        round_manager.finish_round()
        
        # Test starting next round
        test_collections2, control_collections2 = round_manager.start_round()
        
        # Check that collections rotated between rounds
        self.assertEqual(round_manager.current_round, 2)
        
        # Test experiment completion status
        self.assertFalse(round_manager.is_experiment_complete())
        
        # Start round 3
        round_manager.start_round(3)
        round_manager.store_round_results(dummy_results)
        round_manager.finish_round()
        
        # Now experiment should be complete
        self.assertTrue(round_manager.is_experiment_complete())
        
        # Generate cross-round report
        report_path = round_manager.generate_cross_round_report()
        self.assertTrue(os.path.exists(report_path))


if __name__ == "__main__":
    unittest.main()