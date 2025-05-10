#!/usr/bin/env python3
"""Comprehensive Experiment Runner for Ablation Studies.

This module integrates the test/control groups, power set generation,
and multi-round functionality into a comprehensive experimental design
for scientific ablation testing.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from research.ablation.ablation_tester import AblationConfig, AblationTester
from research.ablation.experimental.power_set_generator import PowerSetGenerator
from research.ablation.experimental.round_manager import RoundManager
from research.ablation.experimental.test_control_manager import TestControlGroupManager


class ExperimentRunner:
    """Runs comprehensive ablation experiments with scientific rigor.

    This class coordinates the full experimental design, including:
    - Test/control group separation
    - Power-set testing of collection combinations
    - Multiple test rounds with collection rotation
    - Statistical analysis across rounds
    - Comprehensive reporting
    """

    def __init__(
        self,
        collections: List[str],
        output_dir: str,
        rounds: int = 3,
        control_percentage: float = 0.2,
        combination_limit: int = 100,
        seed: int = 42,
    ):
        """Initialize the experiment runner.

        Args:
            collections: List of collection names to test
            output_dir: Base directory for experiment output
            rounds: Number of experimental rounds to run
            control_percentage: Percentage of queries for control group
            combination_limit: Maximum number of collection combinations to test
            seed: Random seed for reproducible experiments
        """
        self.logger = logging.getLogger(__name__)
        
        if not collections:
            self.logger.error("CRITICAL: No collections provided")
            sys.exit(1)  # Fail-stop immediately
            
        self.collections = collections
        self.output_dir = output_dir
        self.rounds = rounds
        self.control_percentage = control_percentage
        self.combination_limit = combination_limit
        self.seed = seed
        
        # Initialize subcomponents
        self.round_manager = RoundManager(
            collections=collections,
            base_output_dir=output_dir,
            rounds=rounds,
            control_percentage=control_percentage,
            seed=seed,
        )
        
        self.power_set_generator = PowerSetGenerator(
            collections=collections,
            seed=seed,
        )
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # State tracking
        self.ablation_tester = None
        self.current_round = 0
        self.experiment_results = {}
        
        # Track overall experiment statistics
        self.experiment_stats = {
            "rounds_completed": 0,
            "total_ablations": 0,
            "total_queries": 0,
            "experiment_start": datetime.now().isoformat(),
        }
        
        self.logger.info(f"Initialized ExperimentRunner with {len(collections)} collections")
        self.logger.info(f"Planning {rounds} rounds with {combination_limit} max combinations")
        self.logger.info(f"Experiment output directory: {output_dir}")

    def initialize_ablation_tester(self) -> AblationTester:
        """Initialize or reinitialize the ablation tester.

        Returns:
            AblationTester: The initialized ablation tester
        """
        # Create a new ablation tester instance
        self.ablation_tester = AblationTester()
        return self.ablation_tester

    def run_experiment(self) -> bool:
        """Run the complete ablation experiment.

        Returns:
            bool: True if experiment completed successfully
        """
        self.logger.info("=== Starting Comprehensive Ablation Experiment ===")
        
        try:
            # Run each experimental round
            for round_num in range(1, self.rounds + 1):
                self.run_round(round_num)
                
            # Generate cross-round analysis
            self.generate_final_report()
            
            self.logger.info("=== Experiment Completed Successfully ===")
            return True
            
        except Exception as e:
            self.logger.exception(f"CRITICAL: Experiment failed: {e}")
            return False

    def run_round(self, round_number: int) -> bool:
        """Run a single experimental round.

        Args:
            round_number: The round number to run

        Returns:
            bool: True if round completed successfully
        """
        self.logger.info(f"=== Starting Experimental Round {round_number}/{self.rounds} ===")
        
        # Start the round in the round manager
        test_collections, control_collections = self.round_manager.start_round(round_number)
        self.current_round = round_number
        
        # Initialize the ablation tester for this round
        ablation_tester = self.initialize_ablation_tester()
        
        # Get round output directory
        round_dir = self.round_manager.get_round_output_dir()
        
        # Generate combinations to test using power set generator
        # For test group collections only
        combinations = self._generate_test_combinations(test_collections)
        
        # Track round results
        round_results = {
            "round": round_number,
            "start_time": datetime.now().isoformat(),
            "test_collections": test_collections,
            "control_collections": control_collections,
            "combination_count": len(combinations),
            "impact_metrics": {},
            "query_metrics": {},
        }
        
        # Run ablation tests for each combination
        round_impact_metrics = {}
        
        for i, collection_combo in enumerate(combinations):
            self.logger.info(
                f"Testing combination {i+1}/{len(combinations)}: {', '.join(collection_combo)}"
            )
            
            # Configure the ablation test
            config = AblationConfig(
                collections_to_ablate=collection_combo,
                query_limit=100,
                include_metrics=True,
                include_execution_time=True,
                verbose=True,
            )
            
            # Run ablation tests
            # Need to implement integration with ablation_tester.run_ablation_test
            # This will depend on the query generation mechanism
            
            # Store results
            combo_key = "_".join(collection_combo)
            round_impact_metrics[combo_key] = {}  # Replace with actual results
            
        # Store round results
        round_results["impact_metrics"] = round_impact_metrics
        round_results["end_time"] = datetime.now().isoformat()
        
        # Save results
        self.round_manager.store_round_results(round_results)
        self.experiment_results[round_number] = round_results
        
        # Update experiment statistics
        self.experiment_stats["rounds_completed"] += 1
        self.experiment_stats["total_ablations"] += len(combinations)
        
        # Finish the round
        self.round_manager.finish_round()
        self.logger.info(f"=== Completed Experimental Round {round_number}/{self.rounds} ===")
        
        return True

    def _generate_test_combinations(self, test_collections: List[str]) -> List[List[str]]:
        """Generate combinations of collections to test.

        Args:
            test_collections: List of collections in the test group

        Returns:
            List[List[str]]: List of collection combinations to test
        """
        # Create a power set generator for test collections only
        test_power_set = PowerSetGenerator(collections=test_collections, seed=self.seed)
        
        # For smaller collection sets, test all combinations
        if len(test_collections) <= 4:
            self.logger.info(f"Testing all {2**len(test_collections) - 1} combinations of test collections")
            combinations = test_power_set.generate_all_combinations()
        else:
            # For larger sets, use a smart subset
            self.logger.info(
                f"Using smart subset of approximately {self.combination_limit} combinations"
            )
            combinations = test_power_set.generate_smart_subset(
                target_count=self.combination_limit,
                ensure_all_collections=True,
            )
            
        # Always include single-collection ablations
        single_ablations = test_power_set.get_single_collection_ablations()
        
        # Combine and deduplicate
        all_combinations = combinations.copy()
        for combo in single_ablations:
            if combo not in all_combinations:
                all_combinations.append(combo)
                
        self.logger.info(f"Generated {len(all_combinations)} collection combinations to test")
        return all_combinations

    def generate_final_report(self) -> str:
        """Generate the final comprehensive experiment report.

        Returns:
            str: Path to the generated report
        """
        self.logger.info("Generating final experimental report")
        
        # Get cross-round analysis from the round manager
        cross_round_report = self.round_manager.generate_cross_round_report()
        
        # Create a comprehensive summary report
        report_path = os.path.join(self.output_dir, "experiment_summary.md")
        
        with open(report_path, "w") as f:
            f.write("# Comprehensive Ablation Experiment Summary\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Experimental Design\n\n")
            f.write(f"- Collections tested: {', '.join(self.collections)}\n")
            f.write(f"- Experimental rounds: {self.rounds}\n")
            f.write(f"- Control group percentage: {self.control_percentage * 100:.1f}%\n")
            f.write(f"- Max combinations per round: {self.combination_limit}\n\n")
            
            f.write("## Experiment Statistics\n\n")
            f.write(f"- Total ablation tests: {self.experiment_stats['total_ablations']}\n")
            
            # Calculate experiment duration
            if "experiment_start" in self.experiment_stats:
                start_time = datetime.fromisoformat(self.experiment_stats["experiment_start"])
                duration = datetime.now() - start_time
                f.write(f"- Experiment duration: {duration}\n\n")
            
            f.write("## Key Findings\n\n")
            # Add key findings summary here
            # This would typically include:
            # - Collections with highest impact on query results
            # - Most significant cross-collection relationships
            # - Statistical significance of findings
            
            f.write("\n## Statistical Robustness\n\n")
            # Add information about statistical robustness from multiple rounds
            
        self.logger.info(f"Generated experiment summary report: {report_path}")
        return report_path

    def visualize_experiment_results(self) -> List[str]:
        """Generate comprehensive visualizations for experiment results.

        Returns:
            List[str]: Paths to generated visualization files
        """
        self.logger.info("Generating experiment visualizations")
        
        # This would create experiment-wide visualizations
        # Placeholder for now
        return []