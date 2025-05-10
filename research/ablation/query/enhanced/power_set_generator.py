#!/usr/bin/env python
"""
Power set generator for cross-collection queries in ablation testing.

This module provides functions to generate all combinations of collections
for comprehensive testing of cross-collection relationships.
"""

import logging
import sys
from itertools import combinations
from typing import List, Set, Any

from research.ablation.models.activity import ActivityType


def generate_power_set(collections: List[Any]) -> List[List[Any]]:
    """
    Generate all possible combinations of collections (power set minus empty set).
    
    Args:
        collections: List of collection names or ActivityType enums
        
    Returns:
        List of lists, each containing a combination of collection names/types
    """
    if not collections:
        logging.critical("CRITICAL: No collections provided to power set generator")
        sys.exit(1)  # Fail-stop immediately
        
    n = len(collections)
    power_set = []
    
    # Generate all possible combinations (2^n - 1 combinations excluding empty set)
    for i in range(1, 2**n):
        combo = []
        for j in range(n):
            if (i & (1 << j)) > 0:
                combo.append(collections[j])
        power_set.append(combo)
    
    return power_set


def generate_activity_type_combinations(include_single: bool = True) -> List[List[ActivityType]]:
    """
    Generate all combinations of ActivityType enums for cross-collection testing.
    
    Args:
        include_single: Whether to include single-collection combinations (default: True)
        
    Returns:
        List of lists, each containing a combination of ActivityType enums
    """
    # All activity types
    activity_types = [
        ActivityType.MUSIC,
        ActivityType.LOCATION,
        ActivityType.TASK,
        ActivityType.COLLABORATION,
        ActivityType.STORAGE,
        ActivityType.MEDIA
    ]
    
    combinations_list = []
    
    # Generate combinations of different sizes
    for r in range(1 if include_single else 2, len(activity_types) + 1):
        # Generate all combinations of size r
        for combo in combinations(activity_types, r):
            combinations_list.append(list(combo))
    
    return combinations_list


def get_activity_type_pairs() -> List[List[ActivityType]]:
    """
    Get all pairs of activity types for cross-collection testing.
    
    Returns:
        List of pairs of ActivityType enums
    """
    return generate_activity_type_combinations(include_single=False)


def get_semantically_valid_combinations() -> List[List[ActivityType]]:
    """
    Get semantically valid combinations of activity types.
    
    Some combinations may not make sense in a real-world context.
    This function returns only combinations that have meaningful relationships.
    
    Returns:
        List of semantically valid combinations of ActivityType enums
    """
    # Define valid pairs (these have meaningful relationships)
    valid_pairs = [
        [ActivityType.TASK, ActivityType.COLLABORATION],
        [ActivityType.LOCATION, ActivityType.COLLABORATION],
        [ActivityType.MUSIC, ActivityType.LOCATION],
        [ActivityType.STORAGE, ActivityType.TASK],
        [ActivityType.MEDIA, ActivityType.MUSIC],
        [ActivityType.STORAGE, ActivityType.MEDIA],
        [ActivityType.LOCATION, ActivityType.MEDIA],
        [ActivityType.TASK, ActivityType.MEDIA],
        [ActivityType.COLLABORATION, ActivityType.MUSIC],
        [ActivityType.LOCATION, ActivityType.TASK],
        [ActivityType.TASK, ActivityType.MUSIC],
        [ActivityType.LOCATION, ActivityType.STORAGE],
        [ActivityType.COLLABORATION, ActivityType.STORAGE],
        [ActivityType.MEDIA, ActivityType.TASK],
        [ActivityType.MUSIC, ActivityType.MEDIA],
    ]
    
    # Single activity types are always valid
    valid_combinations = []
    for activity_type in ActivityType:
        valid_combinations.append([activity_type])
    
    # Add all valid pairs
    valid_combinations.extend(valid_pairs)
    
    # Generate combinations of 3 or more only if all pairs within are valid
    all_combinations = generate_activity_type_combinations(include_single=False)
    
    for combo in all_combinations:
        if len(combo) > 2:
            # Check if all pairs within this combination are valid
            all_pairs_valid = True
            
            # Generate all pairs in this combination
            for i in range(len(combo)):
                for j in range(i + 1, len(combo)):
                    pair = [combo[i], combo[j]]
                    
                    # Check if this pair is in valid_pairs (in either order)
                    if (pair not in valid_pairs and 
                        [pair[1], pair[0]] not in valid_pairs):
                        all_pairs_valid = False
                        break
                
                if not all_pairs_valid:
                    break
            
            if all_pairs_valid:
                valid_combinations.append(combo)
    
    return valid_combinations


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    
    # Generate and print all combinations
    all_combos = generate_activity_type_combinations()
    logger.info(f"Generated {len(all_combos)} total combinations")
    
    # Generate and print pairs
    pairs = get_activity_type_pairs()
    logger.info(f"Generated {len(pairs)} activity type pairs")
    
    # Generate and print semantically valid combinations
    valid_combos = get_semantically_valid_combinations()
    logger.info(f"Generated {len(valid_combos)} semantically valid combinations")
    
    # Print some examples
    logger.info("\nExample valid combinations:")
    for i, combo in enumerate(valid_combos[:10]):
        logger.info(f"{i+1}. {[a_type.name for a_type in combo]}")