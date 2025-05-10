#!/usr/bin/env python3
"""Round Manager for Multi-Round Ablation Experiments.

This module implements round management for scientific ablation experiments,
providing rotation of collections between test and control groups across rounds.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from research.ablation.experimental.test_control_manager import TestControlGroupManager


class RoundManager:
    """Manages multiple rounds of ablation experiments.

    This class provides functionality to coordinate multiple test rounds,
    including collection rotation, result tracking, and cross-round analysis.
    It ensures that collections rotate between test and control groups for
    complete experimental coverage.
    """

    def __init__(
        self,
        collections: List[str],
        base_output_dir: str,
        rounds: int = 3,
        control_percentage: float = 0.2,
        seed: int = 42,
    ):
        """Initialize the round manager.

        Args:
            collections: List of collection names to test
            base_output_dir: Base directory for round-specific outputs
            rounds: Number of rounds to run
            control_percentage: Percentage of queries for control group
            seed: Random seed for reproducible experimental design
        """
        self.logger = logging.getLogger(__name__)
        
        if not collections:
            self.logger.error("CRITICAL: No collections provided")
            sys.exit(1)  # Fail-stop immediately
            
        if rounds < 1:
            self.logger.error(f"CRITICAL: Invalid number of rounds: {rounds}")
            sys.exit(1)  # Fail-stop immediately
            
        self.collections = collections
        self.base_output_dir = base_output_dir
        self.rounds = rounds
        self.control_percentage = control_percentage
        self.seed = seed
        
        # Initialize random generators
        np.random.seed(seed)
        
        # Current round state
        self.current_round = 0
        self.round_results = {}
        self.round_output_dirs = {}
        
        # Initialize test/control manager
        self.group_manager = TestControlGroupManager(
            collections=collections,
            control_percentage=control_percentage,
            seed=seed,
        )
        
        # Make sure base output directory exists
        os.makedirs(base_output_dir, exist_ok=True)
        
        self.logger.info(f"Initialized RoundManager with {len(collections)} collections")
        self.logger.info(f"Planning {rounds} experimental rounds")
        self.logger.info(f"Base output directory: {base_output_dir}")

    def start_round(self, round_number: Optional[int] = None) -> Tuple[List[str], List[str]]:
        """Start a new experimental round.

        Args:
            round_number: Specific round to start (None = next round)

        Returns:
            Tuple[List[str], List[str]]: (test_collections, control_collections)
        """
        # If round number not specified, use next round
        if round_number is None:
            round_number = self.current_round + 1
            
        # Validate round number
        if round_number < 1 or round_number > self.rounds:
            self.logger.error(f"CRITICAL: Invalid round number: {round_number}")
            sys.exit(1)  # Fail-stop immediately
            
        # Update current round
        self.current_round = round_number
        
        # Create round-specific output directory
        round_dir = os.path.join(self.base_output_dir, f"round_{round_number}")
        os.makedirs(round_dir, exist_ok=True)
        self.round_output_dirs[round_number] = round_dir
        
        # First round: Initialize test/control group assignments
        if round_number == 1:
            control_count = max(1, int(len(self.collections) * self.control_percentage))
            test_collections, control_collections = self.group_manager.assign_collections(
                control_count=control_count
            )
        else:
            # Subsequent rounds: Rotate collections between groups
            # Use simple approach of rotating 2 collections per round
            rotations = 2
            test_collections, control_collections = self.group_manager.rotate_collections(
                collections_to_rotate=rotations
            )
            
        self.logger.info(f"=== Starting Round {round_number}/{self.rounds} ===")
        self.logger.info(f"Test collections: {', '.join(test_collections)}")
        self.logger.info(f"Control collections: {', '.join(control_collections)}")
        
        return test_collections, control_collections

    def get_round_output_dir(self) -> str:
        """Get the output directory for the current round.

        Returns:
            str: Path to the current round's output directory
        """
        if self.current_round not in self.round_output_dirs:
            self.logger.error(f"CRITICAL: No output directory for round {self.current_round}")
            sys.exit(1)  # Fail-stop immediately
            
        return self.round_output_dirs[self.current_round]

    def store_round_results(self, results: Dict) -> None:
        """Store results for the current round.

        Args:
            results: Dictionary of results from the current round
        """
        if not self.current_round:
            self.logger.error("CRITICAL: Cannot store results - no active round")
            sys.exit(1)  # Fail-stop immediately
            
        # Add metadata
        results_with_metadata = {
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            "test_collections": self.group_manager.get_test_collections(),
            "control_collections": self.group_manager.get_control_collections(),
            "results": results,
        }
        
        # Store in memory
        self.round_results[self.current_round] = results_with_metadata
        
        # Save to disk
        output_file = os.path.join(
            self.round_output_dirs[self.current_round],
            "round_results.json"
        )
        
        with open(output_file, "w") as f:
            json.dump(
                results_with_metadata,
                f,
                indent=2,
                default=lambda o: str(o) if isinstance(o, (uuid.UUID, set)) else o,
            )
            
        self.logger.info(f"Saved round {self.current_round} results to {output_file}")

    def finish_round(self) -> None:
        """Finish the current round and prepare for the next one."""
        if not self.current_round:
            self.logger.error("CRITICAL: No active round to finish")
            sys.exit(1)  # Fail-stop immediately
            
        if self.current_round not in self.round_results:
            self.logger.error(f"CRITICAL: No results for round {self.current_round}")
            sys.exit(1)  # Fail-stop immediately
            
        self.logger.info(f"=== Finished Round {self.current_round}/{self.rounds} ===")
        
        # Generate round-specific reports
        self._generate_round_report(self.current_round)

    def _generate_round_report(self, round_number: int) -> None:
        """Generate a report for a specific round.

        Args:
            round_number: The round number to report on
        """
        if round_number not in self.round_results:
            self.logger.error(f"CRITICAL: No results for round {round_number}")
            sys.exit(1)  # Fail-stop immediately
            
        # Get round data
        round_data = self.round_results[round_number]
        output_dir = self.round_output_dirs[round_number]
        
        # Create markdown report
        report_path = os.path.join(output_dir, f"round_{round_number}_report.md")
        
        with open(report_path, "w") as f:
            f.write(f"# Ablation Study - Round {round_number} Report\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Experimental Design\n\n")
            f.write(f"- Test collections: {', '.join(round_data['test_collections'])}\n")
            f.write(f"- Control collections: {', '.join(round_data['control_collections'])}\n\n")
            
            # Add experiment-specific details from the results
            if "queries_tested" in round_data["results"]:
                f.write(f"- Queries tested: {round_data['results']['queries_tested']}\n")
            if "ablations_performed" in round_data["results"]:
                f.write(f"- Ablations performed: {round_data['results']['ablations_performed']}\n\n")
            
            f.write("## Summary Results\n\n")
            # Add round-specific summary information here
            
        self.logger.info(f"Generated report for round {round_number}: {report_path}")

    def is_experiment_complete(self) -> bool:
        """Check if all rounds have been completed.

        Returns:
            bool: True if all rounds are complete
        """
        return self.current_round == self.rounds and self.current_round in self.round_results

    def generate_cross_round_report(self) -> str:
        """Generate a comprehensive report across all rounds.

        Returns:
            str: Path to the generated report
        """
        if not self.is_experiment_complete():
            self.logger.warning("Generating cross-round report before experiment completion")
            
        # Create a report that compares results across rounds
        report_path = os.path.join(self.base_output_dir, "cross_round_analysis.md")
        
        with open(report_path, "w") as f:
            f.write("# Cross-Round Ablation Analysis\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Experimental Design\n\n")
            f.write(f"- Total rounds: {self.rounds}\n")
            f.write(f"- Collections tested: {', '.join(self.collections)}\n")
            f.write(f"- Control percentage: {self.control_percentage * 100:.1f}%\n\n")
            
            f.write("## Round Summary\n\n")
            f.write("| Round | Test Collections | Control Collections |\n")
            f.write("|-------|-----------------|---------------------|\n")
            
            for r in range(1, self.rounds + 1):
                if r in self.round_results:
                    test_cols = ', '.join(self.round_results[r]['test_collections'])
                    control_cols = ', '.join(self.round_results[r]['control_collections'])
                    f.write(f"| {r} | {test_cols} | {control_cols} |\n")
                    
            f.write("\n## Statistical Analysis\n\n")
            # Add cross-round statistical analysis here
            
            f.write("\n## Consistency Analysis\n\n")
            f.write("Analysis of result consistency across rounds:\n\n")
            # Add consistency analysis here
            
        self.logger.info(f"Generated cross-round analysis report: {report_path}")
        return report_path

    def get_statistical_summary(self) -> Dict:
        """Calculate statistical summary across all rounds.

        Returns:
            Dict: Statistical metrics across rounds
        """
        # This would implement statistical analysis across rounds
        # For now, return a placeholder
        return {
            "rounds_completed": len(self.round_results),
            "total_rounds": self.rounds,
        }
        
    def calculate_cross_round_variance(self) -> Dict:
        """Calculate variance metrics across rounds for reliability assessment.

        Returns:
            Dict: Variance metrics for key measurements
        """
        # This would analyze measurement variance across rounds
        # For now, return a placeholder
        return {
            "rounds_analyzed": len(self.round_results),
        }