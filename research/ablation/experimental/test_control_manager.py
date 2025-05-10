#!/usr/bin/env python3
"""Test/Control Group Manager for Ablation Experiments.

This module implements test/control group separation for scientific rigor
in ablation experiments. It ensures unbiased evaluation by maintaining a control
group of queries and collections that are not subject to ablation.
"""

import logging
import random
import sys
import uuid
from typing import Dict, List, Set, Tuple, Union

import numpy as np


class TestControlGroupManager:
    """Manages test and control groups for ablation experiments.

    This class implements the scientific methodology of separating
    queries and collections into test and control groups for proper
    experimental design. The control group serves as a "canary in the coal mine"
    to validate that changes in results are due to ablations, not other factors.
    """

    def __init__(
        self,
        collections: List[str],
        control_percentage: float = 0.2,
        seed: int = 42,
    ):
        """Initialize test/control group manager.

        Args:
            collections: List of collection names to manage
            control_percentage: Percentage of queries to assign to control group (0.0-1.0)
            seed: Random seed for reproducible assignment
        """
        self.logger = logging.getLogger(__name__)
        
        if not collections:
            self.logger.error("CRITICAL: No collections provided to TestControlGroupManager")
            sys.exit(1)  # Fail-stop immediately
            
        if control_percentage < 0.0 or control_percentage > 1.0:
            self.logger.error(f"CRITICAL: Invalid control percentage: {control_percentage}")
            sys.exit(1)  # Fail-stop immediately
            
        self.collections = collections
        self.control_percentage = control_percentage
        self.random_generator = random.Random(seed)
        np.random.seed(seed)  # For numpy operations
        
        # Track assignments
        self.control_queries: Set[str] = set()
        self.test_queries: Set[str] = set()
        
        # Collection assignments (for round rotation)
        self.control_collections: Set[str] = set()
        self.test_collections: Set[str] = set()
        self.test_collections.update(collections)  # Default: all collections in test group
        
        self.logger.info(f"Initialized Test/Control Manager with {len(collections)} collections")
        self.logger.info(f"Control group percentage: {control_percentage * 100:.1f}%")

    def assign_query_group(self, query_id: Union[uuid.UUID, str]) -> str:
        """Assign a query to either the test or control group.

        Args:
            query_id: The UUID of the query to assign

        Returns:
            str: Either "test" or "control"
        """
        query_id_str = str(query_id)
        
        # If already assigned, return the existing assignment
        if query_id_str in self.control_queries:
            return "control"
        if query_id_str in self.test_queries:
            return "test"
            
        # Make a new assignment based on control percentage
        if self.random_generator.random() < self.control_percentage:
            self.control_queries.add(query_id_str)
            self.logger.info(f"Assigned query {query_id_str} to CONTROL group")
            return "control"
        else:
            self.test_queries.add(query_id_str)
            self.logger.info(f"Assigned query {query_id_str} to TEST group")
            return "test"

    def is_control_query(self, query_id: Union[uuid.UUID, str]) -> bool:
        """Check if a query is in the control group.

        Args:
            query_id: The UUID of the query to check

        Returns:
            bool: True if in control group, False otherwise
        """
        return str(query_id) in self.control_queries

    def is_test_query(self, query_id: Union[uuid.UUID, str]) -> bool:
        """Check if a query is in the test group.

        Args:
            query_id: The UUID of the query to check

        Returns:
            bool: True if in test group, False otherwise
        """
        return str(query_id) in self.test_queries

    def get_control_collections(self) -> List[str]:
        """Get all collections in the control group.

        Returns:
            List[str]: List of collection names in control group
        """
        return list(self.control_collections)

    def get_test_collections(self) -> List[str]:
        """Get all collections in the test group.

        Returns:
            List[str]: List of collection names in test group
        """
        return list(self.test_collections)

    def assign_collections(self, control_count: int = None) -> Tuple[List[str], List[str]]:
        """Assign collections to test and control groups.

        Args:
            control_count: Number of collections to put in control group
                          (if None, uses control_percentage)

        Returns:
            Tuple[List[str], List[str]]: (test_collections, control_collections)
        """
        # Calculate control count if not specified
        if control_count is None:
            control_count = max(1, int(len(self.collections) * self.control_percentage))
            
        # Validate control count
        if control_count <= 0 or control_count >= len(self.collections):
            self.logger.error(
                f"CRITICAL: Invalid control count {control_count} for {len(self.collections)} collections"
            )
            sys.exit(1)  # Fail-stop immediately
            
        # Randomly select control collections
        all_collections = self.collections.copy()
        self.random_generator.shuffle(all_collections)
        control_collections = all_collections[:control_count]
        test_collections = all_collections[control_count:]
        
        # Update internal state
        self.control_collections = set(control_collections)
        self.test_collections = set(test_collections)
        
        self.logger.info(f"Assigned {len(test_collections)} collections to TEST group")
        self.logger.info(f"Assigned {len(control_collections)} collections to CONTROL group")
        self.logger.info(f"Test collections: {', '.join(test_collections)}")
        self.logger.info(f"Control collections: {', '.join(control_collections)}")
        
        return test_collections, control_collections

    def rotate_collections(self, collections_to_rotate: int = None) -> Tuple[List[str], List[str]]:
        """Rotate collections between test and control groups between rounds.
        
        This ensures that each collection gets tested in both the test and
        control groups, which is important for complete experimental design.

        Args:
            collections_to_rotate: Number of collections to rotate (if None, rotates half)

        Returns:
            Tuple[List[str], List[str]]: (test_collections, control_collections) after rotation
        """
        # If no explicit count, rotate half of the smaller group
        if collections_to_rotate is None:
            collections_to_rotate = max(1, min(
                len(self.test_collections) // 2,
                len(self.control_collections) // 2
            ))
            
        # Validate rotation count
        if collections_to_rotate <= 0:
            self.logger.warning(f"Invalid rotation count {collections_to_rotate}, using 1")
            collections_to_rotate = 1
            
        if (collections_to_rotate > len(self.test_collections) or 
            collections_to_rotate > len(self.control_collections)):
            self.logger.warning(
                f"Rotation count {collections_to_rotate} too large, capping to maximum possible"
            )
            collections_to_rotate = min(len(self.test_collections), len(self.control_collections))
            
        # Select collections to move from test to control
        test_collections = list(self.test_collections)
        self.random_generator.shuffle(test_collections)
        moving_to_control = test_collections[:collections_to_rotate]
        remaining_test = test_collections[collections_to_rotate:]
        
        # Select collections to move from control to test
        control_collections = list(self.control_collections)
        self.random_generator.shuffle(control_collections)
        moving_to_test = control_collections[:collections_to_rotate]
        remaining_control = control_collections[collections_to_rotate:]
        
        # Update internal state
        self.test_collections = set(remaining_test + moving_to_test)
        self.control_collections = set(remaining_control + moving_to_control)
        
        self.logger.info(f"Rotated {collections_to_rotate} collections between test and control groups")
        self.logger.info(f"Moved to control: {', '.join(moving_to_control)}")
        self.logger.info(f"Moved to test: {', '.join(moving_to_test)}")
        
        # Return new assignments
        return list(self.test_collections), list(self.control_collections)

    def is_control_collection(self, collection_name: str) -> bool:
        """Check if a collection is in the control group.

        Args:
            collection_name: The name of the collection to check

        Returns:
            bool: True if in control group, False otherwise
        """
        return collection_name in self.control_collections

    def is_test_collection(self, collection_name: str) -> bool:
        """Check if a collection is in the test group.

        Args:
            collection_name: The name of the collection to check

        Returns:
            bool: True if in test group, False otherwise
        """
        return collection_name in self.test_collections

    def get_group_statistics(self) -> Dict[str, Dict[str, int]]:
        """Get statistics about the test/control groups.
        
        Returns:
            Dict with query and collection counts for test and control groups
        """
        return {
            "queries": {
                "test": len(self.test_queries),
                "control": len(self.control_queries),
                "total": len(self.test_queries) + len(self.control_queries),
            },
            "collections": {
                "test": len(self.test_collections),
                "control": len(self.control_collections),
                "total": len(self.test_collections) + len(self.control_collections),
            }
        }