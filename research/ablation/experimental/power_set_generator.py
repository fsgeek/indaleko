#!/usr/bin/env python3
"""Power Set Generator for Ablation Experiments.

This module implements power set generation for ablation testing,
allowing experiments to test all possible combinations of collections.
"""

import itertools
import logging
import random
import sys
from typing import List, Optional, Set


class PowerSetGenerator:
    """Generates power sets (all possible combinations) of collections.

    This class provides methods to generate all possible combinations
    of collections for comprehensive ablation testing, with options to
    limit the combination size or generate smart subsets for efficiency.
    """

    def __init__(self, collections: List[str], seed: int = 42):
        """Initialize the power set generator.

        Args:
            collections: List of collection names to generate combinations from
            seed: Random seed for reproducible sampling
        """
        self.logger = logging.getLogger(__name__)
        
        if not collections:
            self.logger.error("CRITICAL: No collections provided to PowerSetGenerator")
            sys.exit(1)  # Fail-stop immediately
            
        self.collections = sorted(collections)  # Sort for deterministic output
        self.random_generator = random.Random(seed)
        
        self.logger.info(f"Initialized PowerSetGenerator with {len(collections)} collections")

    def generate_all_combinations(
        self, 
        min_size: int = 1, 
        max_size: Optional[int] = None,
    ) -> List[List[str]]:
        """Generate all possible combinations of collections.

        Args:
            min_size: Minimum number of collections in a combination
            max_size: Maximum number of collections in a combination
                     (if None, uses all collections)

        Returns:
            List of all possible collection combinations
        """
        if max_size is None:
            max_size = len(self.collections)
            
        # Validate size parameters
        if min_size < 1:
            self.logger.error(f"CRITICAL: min_size must be at least 1, got {min_size}")
            sys.exit(1)  # Fail-stop immediately
            
        if max_size > len(self.collections):
            self.logger.warning(
                f"max_size {max_size} exceeds collection count, capping at {len(self.collections)}"
            )
            max_size = len(self.collections)
            
        if min_size > max_size:
            self.logger.error(f"CRITICAL: min_size ({min_size}) exceeds max_size ({max_size})")
            sys.exit(1)  # Fail-stop immediately
        
        # Generate all combinations of sizes from min_size to max_size
        all_combinations = []
        for size in range(min_size, max_size + 1):
            combinations = list(itertools.combinations(self.collections, size))
            all_combinations.extend([list(combo) for combo in combinations])
            
        self.logger.info(
            f"Generated {len(all_combinations)} combinations with sizes {min_size} to {max_size}"
        )
        return all_combinations

    def generate_smart_subset(
        self,
        target_count: int,
        min_size: int = 1,
        max_size: Optional[int] = None,
        ensure_all_collections: bool = True,
    ) -> List[List[str]]:
        """Generate a smart subset of combinations for efficient testing.
        
        This method creates a smaller set of combinations that still
        provides good coverage for ablation testing, prioritizing diverse
        combinations with varying sizes.

        Args:
            target_count: Target number of combinations to generate
            min_size: Minimum combination size
            max_size: Maximum combination size (None = all collections)
            ensure_all_collections: Ensure each collection appears at least once

        Returns:
            List of selected collection combinations
        """
        if max_size is None:
            max_size = len(self.collections)
            
        # Validate parameters
        if target_count < 1:
            self.logger.error(f"CRITICAL: target_count must be at least 1, got {target_count}")
            sys.exit(1)  # Fail-stop immediately
            
        # Generate all combinations
        all_combinations = self.generate_all_combinations(min_size, max_size)
        
        # If target count exceeds available combinations, return all
        if target_count >= len(all_combinations):
            self.logger.info(
                f"target_count {target_count} exceeds available combinations, returning all {len(all_combinations)}"
            )
            return all_combinations
            
        # Track which collections are covered
        covered_collections: Set[str] = set()
        selected_combinations: List[List[str]] = []
        
        # First, ensure all collections are covered (if requested)
        if ensure_all_collections:
            # Shuffle combinations to randomize selection
            shuffled_combinations = all_combinations.copy()
            self.random_generator.shuffle(shuffled_combinations)
            
            # Keep selecting combinations until all collections are covered
            for combo in shuffled_combinations:
                if all(c in covered_collections for c in self.collections):
                    break
                    
                # Check if this combo adds any uncovered collections
                new_collections = set(combo) - covered_collections
                if new_collections:
                    selected_combinations.append(combo)
                    covered_collections.update(combo)
            
            self.logger.info(
                f"Selected {len(selected_combinations)} combinations to ensure all collections are covered"
            )
            
        # If we still need more combinations to reach target count
        remaining_count = target_count - len(selected_combinations)
        if remaining_count > 0:
            # Filter out already selected combinations
            remaining_combinations = [
                combo for combo in all_combinations if combo not in selected_combinations
            ]
            
            # Randomly select additional combinations
            if remaining_combinations:
                additional_selections = self.random_generator.sample(
                    remaining_combinations, 
                    min(remaining_count, len(remaining_combinations))
                )
                selected_combinations.extend(additional_selections)
                
        self.logger.info(f"Selected a total of {len(selected_combinations)} combinations")
        return selected_combinations

    def generate_balanced_subset(
        self, 
        combinations_per_size: int,
        min_size: int = 1,
        max_size: Optional[int] = None,
    ) -> List[List[str]]:
        """Generate a subset with balanced representation of different sizes.

        Args:
            combinations_per_size: Number of combinations to select for each size
            min_size: Minimum combination size
            max_size: Maximum combination size (None = all collections)

        Returns:
            List of selected combinations with balanced size distribution
        """
        if max_size is None:
            max_size = len(self.collections)
            
        # Validate parameters
        if combinations_per_size < 1:
            self.logger.error(
                f"CRITICAL: combinations_per_size must be at least 1, got {combinations_per_size}"
            )
            sys.exit(1)  # Fail-stop immediately
            
        balanced_combinations = []
        
        # For each size, select a specific number of combinations
        for size in range(min_size, max_size + 1):
            # Generate all combinations of current size
            size_combinations = list(itertools.combinations(self.collections, size))
            
            # If we have fewer combinations than requested, take all of them
            if len(size_combinations) <= combinations_per_size:
                selected = size_combinations
            else:
                # Randomly sample the requested number
                selected = self.random_generator.sample(size_combinations, combinations_per_size)
                
            # Add to our balanced selection
            balanced_combinations.extend([list(combo) for combo in selected])
            
            self.logger.info(
                f"Selected {len(selected)} combinations of size {size} (out of {len(size_combinations)} possible)"
            )
            
        self.logger.info(f"Generated a balanced subset with {len(balanced_combinations)} total combinations")
        return balanced_combinations

    def get_single_collection_ablations(self) -> List[List[str]]:
        """Get combinations representing single collection ablations.
        
        This returns combinations where only one collection is ablated,
        which is useful for measuring the direct impact of each collection.

        Returns:
            List of combinations, each with all but one collection
        """
        result = []
        for i in range(len(self.collections)):
            ablation = self.collections.copy()
            ablation.pop(i)
            result.append(ablation)
            
        self.logger.info(f"Generated {len(result)} single-collection ablation combinations")
        return result

    def get_single_collection_inclusions(self) -> List[List[str]]:
        """Get combinations representing single collection inclusions.
        
        This returns combinations where only one collection is included,
        which is useful for measuring the individual value of each collection.

        Returns:
            List of combinations, each with exactly one collection
        """
        result = [[collection] for collection in self.collections]
        self.logger.info(f"Generated {len(result)} single-collection inclusion combinations")
        return result