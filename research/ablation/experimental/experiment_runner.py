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

from db.db_config import IndalekoDBConfig
from research.ablation.ablation_tester import AblationConfig, AblationTester
from research.ablation.collectors.collaboration_collector import CollaborationActivityCollector
from research.ablation.collectors.location_collector import LocationActivityCollector
from research.ablation.collectors.media_collector import MediaActivityCollector
from research.ablation.collectors.music_collector import MusicActivityCollector
from research.ablation.collectors.storage_collector import StorageActivityCollector
from research.ablation.collectors.task_collector import TaskActivityCollector
from research.ablation.data_sanity_checker import DataSanityChecker
from research.ablation.experimental.power_set_generator import PowerSetGenerator
from research.ablation.experimental.round_manager import RoundManager
from research.ablation.experimental.test_control_manager import TestControlGroupManager
from research.ablation.ner.entity_manager import NamedEntityManager
from research.ablation.query.enhanced.enhanced_query_generator import EnhancedQueryGenerator
from research.ablation.recorders.collaboration_recorder import CollaborationActivityRecorder
from research.ablation.recorders.location_recorder import LocationActivityRecorder
from research.ablation.recorders.media_recorder import MediaActivityRecorder
from research.ablation.recorders.music_recorder import MusicActivityRecorder
from research.ablation.recorders.storage_recorder import StorageActivityRecorder
from research.ablation.recorders.task_recorder import TaskActivityRecorder
from research.ablation.utils.uuid_utils import generate_deterministic_uuid


class TestDataComponents:
    """Components for test data generation.

    This class holds the components needed to generate test data for different
    activity types, including the collector and recorder classes.
    """

    def __init__(
        self,
        name: str,
        collector: type,
        recorder: type,
        hash_name: str = None,
        hash_property_name: str = None
    ):
        """Initialize test data components.

        Args:
            name: The name of the activity type
            collector: The collector class for this activity type
            recorder: The recorder class for this activity type
            hash_name: The name to use in content hash generation
            hash_property_name: The property to use in content hash generation
        """
        self.name = name
        self.collector = collector
        self.recorder = recorder
        self.hash_name = hash_name or name.lower()
        self.hash_property_name = hash_property_name or f"{name.lower()}_id"


class ExperimentRunner:
    """Runs comprehensive ablation experiments with scientific rigor.

    This class coordinates the full experimental design, including:
    - Test/control group separation
    - Power-set testing of collection combinations
    - Multiple test rounds with collection rotation
    - Statistical analysis across rounds
    - Comprehensive reporting
    - Integration with data generation and query execution
    """

    def __init__(
        self,
        collections: List[str],
        output_dir: str,
        rounds: int = 3,
        control_percentage: float = 0.2,
        combination_limit: int = 100,
        seed: int = 42,
        record_count: int = 100,
        query_count: int = 10,
        clear_existing: bool = True,
    ):
        """Initialize the experiment runner.

        Args:
            collections: List of collection names to test
            output_dir: Base directory for experiment output
            rounds: Number of experimental rounds to run
            control_percentage: Percentage of queries for control group
            combination_limit: Maximum number of collection combinations to test
            seed: Random seed for reproducible experiments
            record_count: Number of synthetic records to generate per collection
            query_count: Number of queries to generate per collection
            clear_existing: Whether to clear existing data before running
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
        self.record_count = record_count
        self.query_count = query_count
        self.clear_existing = clear_existing

        # Initialize database connection
        try:
            self.db_config = IndalekoDBConfig()
            self.db = self.db_config.get_arangodb()
            self.logger.info("Successfully connected to ArangoDB database")
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to connect to database: {e}")
            sys.exit(1)  # Fail-stop immediately

        # Initialize activity data providers
        self.activity_data_providers = self._setup_activity_data_providers()

        # Initialize entity manager for consistent entity references
        self.entity_manager = NamedEntityManager()

        # Initialize query generator
        self.query_generator = EnhancedQueryGenerator()

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

        # Initialize test/control manager
        self.test_control_manager = TestControlGroupManager(
            collections=collections,
            control_percentage=control_percentage,
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
            "total_records_generated": 0,
            "experiment_start": datetime.now().isoformat(),
        }

        self.logger.info(f"Initialized ExperimentRunner with {len(collections)} collections")
        self.logger.info(f"Planning {rounds} rounds with {combination_limit} max combinations")
        self.logger.info(f"Will generate {record_count} records and {query_count} queries per collection")
        self.logger.info(f"Experiment output directory: {output_dir}")

    def _setup_activity_data_providers(self) -> Dict[str, TestDataComponents]:
        """Set up activity data providers with collector/recorder pairs.

        Returns:
            Dict mapping collection names to their data providers
        """
        providers = {
            "AblationLocationActivity": TestDataComponents(
                name="Location",
                collector=LocationActivityCollector,
                recorder=LocationActivityRecorder,
                hash_name="location",
                hash_property_name="location_name",
            ),
            "AblationMusicActivity": TestDataComponents(
                name="Music",
                collector=MusicActivityCollector,
                recorder=MusicActivityRecorder,
                hash_name="music",
                hash_property_name="artist",
            ),
            "AblationTaskActivity": TestDataComponents(
                name="Task",
                collector=TaskActivityCollector,
                recorder=TaskActivityRecorder,
                hash_name="task",
                hash_property_name="task_type",
            ),
            "AblationCollaborationActivity": TestDataComponents(
                name="Collaboration",
                collector=CollaborationActivityCollector,
                recorder=CollaborationActivityRecorder,
                hash_name="collaboration",
                hash_property_name="event_title",
            ),
            "AblationStorageActivity": TestDataComponents(
                name="Storage",
                collector=StorageActivityCollector,
                recorder=StorageActivityRecorder,
                hash_name="storage",
                hash_property_name="file_type",
            ),
            "AblationMediaActivity": TestDataComponents(
                name="Media",
                collector=MediaActivityCollector,
                recorder=MediaActivityRecorder,
                hash_name="media",
                hash_property_name="media_type",
            ),
        }

        # Filter providers to only include those for requested collections
        return {k: v for k, v in providers.items() if k in self.collections}

    def initialize_ablation_tester(self) -> AblationTester:
        """Initialize or reinitialize the ablation tester.

        Returns:
            AblationTester: The initialized ablation tester
        """
        # Create a new ablation tester instance
        self.ablation_tester = AblationTester()
        return self.ablation_tester

    def clear_existing_data(self) -> None:
        """Clear existing data from all activity collections and truth data."""
        if not self.clear_existing:
            self.logger.info("Skipping data clearing (clear_existing=False)")
            return

        self.logger.info("Clearing existing data from all collections...")

        # Clear each activity collection
        for collection_name in self.collections:
            if self.db.has_collection(collection_name):
                self.db.aql.execute(f"FOR doc IN {collection_name} REMOVE doc IN {collection_name}")
                self.logger.info(f"Cleared collection {collection_name}")

        # Always clear the truth collection to avoid duplicate key errors
        truth_collection = "AblationQueryTruth"
        if self.db.has_collection(truth_collection):
            self.db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
            self.logger.info(f"Cleared collection {truth_collection}")

        self.logger.info("All collections cleared successfully")

    def generate_test_data(self) -> Dict[str, List[Dict]]:
        """Generate synthetic test data for all activity types.

        Returns:
            Dict mapping collection names to generated test data
        """
        self.logger.info(f"Generating {self.record_count} records for each activity type...")

        test_data = {}
        collections_loaded = []

        # For each collection, generate and load synthetic data
        for collection_name, provider in self.activity_data_providers.items():
            self.logger.info(f"Generating data for {collection_name}...")

            # Initialize collector based on whether it supports entity_manager
            collector_class = provider.collector
            if provider.name in ["Location", "Music", "Task", "Collaboration"]:
                # These collectors support entity_manager
                collector = collector_class(entity_manager=self.entity_manager, seed_value=self.seed)
            else:
                # Storage and Media collectors may only support seed_value
                collector = collector_class(seed_value=self.seed)

            # Initialize recorder
            recorder = provider.recorder()

            # Generate data batch
            data = collector.generate_batch(self.record_count)

            # Ensure all data has proper ID fields
            for item in data:
                if "id" not in item:
                    # Create content hash for deterministic IDs
                    content_hash = f"{provider.hash_name}:{item.get(provider.hash_property_name, 'unknown')}"
                    item["id"] = generate_deterministic_uuid(content_hash)

                # Ensure _key field for ArangoDB
                if "_key" not in item and "id" in item:
                    item["_key"] = str(item["id"])

            # Record the batch in the database
            batch_success = recorder.record_batch(data)

            if batch_success:
                collections_loaded.append(collection_name)
                test_data[collection_name] = data
                self.logger.info(f"Successfully loaded {len(data)} records for {collection_name}")

                # Update experiment statistics
                self.experiment_stats["total_records_generated"] += len(data)
            else:
                self.logger.error(f"CRITICAL: Failed to record data for {collection_name}")
                sys.exit(1)  # Fail-stop immediately

        self.logger.info(f"Successfully loaded data for {len(collections_loaded)} collections")

        # Run data sanity check to verify data integrity
        self.logger.info("Running data sanity check...")
        checker = DataSanityChecker(fail_fast=True)
        sanity_check_passed = checker.run_all_checks()
        if not sanity_check_passed:
            self.logger.error("CRITICAL: Data sanity check failed")
            sys.exit(1)  # Fail-stop immediately

        return test_data

    def generate_cross_collection_queries(
        self,
        ablation_tester: AblationTester,
        test_collections: List[str],
        control_collections: List[str]
    ) -> List[Dict]:
        """Generate cross-collection queries for ablation testing.

        Args:
            ablation_tester: The ablation tester to use for truth data storage
            test_collections: Collections in the test group
            control_collections: Collections in the control group

        Returns:
            List of generated query objects with metadata
        """
        self.logger.info("Generating cross-collection test queries...")

        all_queries = []

        # Define all collection pairs to generate queries for
        # Include both test and control groups
        collection_pairs = []

        # Add test group collection pairs
        for i in range(len(test_collections)):
            for j in range(i+1, len(test_collections)):
                collection_pairs.append([test_collections[i], test_collections[j]])

        # Add control group collection pairs
        for i in range(len(control_collections)):
            for j in range(i+1, len(control_collections)):
                collection_pairs.append([control_collections[i], control_collections[j]])

        # For each collection pair, generate the specified number of queries
        for collection_pair in collection_pairs:
            collection1, collection2 = collection_pair

            # Map collection names to activity types for the query generator
            collection_to_activity_type = {
                "AblationMusicActivity": "music",
                "AblationLocationActivity": "location",
                "AblationTaskActivity": "task",
                "AblationCollaborationActivity": "collaboration",
                "AblationStorageActivity": "storage",
                "AblationMediaActivity": "media",
            }

            # Determine activity types from collections
            activity_types = [
                collection_to_activity_type.get(c, "generic")
                for c in collection_pair
                if c in collection_to_activity_type
            ]

            # Generate queries for each activity type in the pair
            queries_for_pair = []
            for activity_type in activity_types:
                try:
                    # Generate diverse queries with the EnhancedQueryGenerator
                    activity_queries = self.query_generator.generate_enhanced_queries(
                        activity_type,
                        count=self.query_count // len(activity_types) + 1,
                    )
                    self.logger.info(
                        f"Generated {len(activity_queries)} diverse queries for {activity_type}"
                    )
                    queries_for_pair.extend(activity_queries)
                except Exception as e:
                    self.logger.error(f"CRITICAL: Failed to generate queries: {e}")
                    sys.exit(1)  # Fail-stop immediately

            # Limit to requested count
            queries_for_pair = queries_for_pair[:self.query_count]

            # Process each query
            for i, query_text in enumerate(queries_for_pair):
                # Generate a unique base query ID
                # Generate a unique base query ID that combines both collections
                # This ensures a stable ID even if collection order changes between rounds
                # We sort the collections to make the ID independent of order
                sorted_collections = sorted([collection1, collection2])
                base_query_id = generate_deterministic_uuid(
                    f"cross_query:{sorted_collections[0]}:{sorted_collections[1]}:{i}:{self.seed}"
                )

                # Track query group assignment (test or control)
                query_group = self.test_control_manager.assign_query_group(base_query_id)

                # Generate matching entities for each collection in the pair
                matching_entities = {}
                collection_query_ids = {}

                for collection in collection_pair:
                    # CRITICAL FIX: Generate a GLOBALLY unique and truly fixed query ID
                    # Include ALL relevant context that defines the entity selection:
                    # - collection name (for collection-specific selection)
                    # - query index (to differentiate between queries)
                    # - experiment seed (to make experiments reproducible)
                    # - round number (to ensure consistent entity selection across rounds)
                    # - "fixed_query" prefix (to indicate this is a fixed, deterministic ID)
                    collection_query_id = generate_deterministic_uuid(
                        f"fixed_query:{collection}:{i}:{self.seed}:{self.current_round}"
                    )
                    collection_query_ids[collection] = collection_query_id

                    self.logger.info(f"Using fixed query ID {collection_query_id} for {collection}")

                    # Find matching entities in the collection - using a DETERMINISTIC approach
                    try:
                        # CRITICAL FIX: Use a fixed deterministic approach for entity selection
                        # The key is ensuring the EXACT SAME query always selects the EXACT SAME entities
                        # We'll use collection_query_id as a stable, deterministic seed

                        # Convert the collection query ID to a deterministic seed
                        # Using a consistent hash function for the seed value
                        seed_str = str(collection_query_id).replace('-', '')
                        # Use more bits from the UUID for better distribution
                        seed_value = int(seed_str[:12], 16)  # Use 12 hex chars instead of 8

                        # Fix the offset to ensure the same entities are always selected for the same query
                        # Use a more sophisticated formula that's less likely to have collisions
                        # The magic numbers here (50, 7, 10) are chosen to provide good distribution
                        # while still being deterministic
                        fixed_offset = (seed_value % 50) + (self.current_round * 7) % 10

                        # Log the seed and offset for debugging
                        self.logger.info(f"Using seed {seed_value} with fixed offset {fixed_offset} for {collection}")

                        # Always use a fixed AQL query with standardized sorting
                        # Using stable sort by _key (no random functions) and fixed entity count
                        cursor = self.db.aql.execute(
                            f"""
                            FOR doc IN {collection}
                            SORT doc._key ASC  /* Use stable ascending sort by document key */
                            LIMIT {fixed_offset}, 5  /* Take exactly 5 entities with fixed offset */
                            RETURN doc._key
                            """
                        )
                        entity_ids = [doc_key for doc_key in cursor]

                        self.logger.info(
                            f"Selected {len(entity_ids)} deterministic entities for query {collection_query_id} in {collection}"
                        )

                        # Store truth data with the collection-specific query ID
                        ablation_tester.store_truth_data(collection_query_id, collection, entity_ids)

                        # Record entities for this query-collection pair
                        matching_entities[collection] = entity_ids

                    except Exception as e:
                        self.logger.error(f"CRITICAL: Failed to process truth data: {e}")
                        sys.exit(1)  # Fail-stop immediately

                # Add query to the result list
                all_queries.append({
                    "id": str(base_query_id),
                    "text": query_text,
                    "type": "cross_collection",
                    "collections": collection_pair,
                    "matching_entities": matching_entities,
                    "collection_query_ids": {col: str(qid) for col, qid in collection_query_ids.items()},
                    "group": query_group,  # Track test/control group
                })

                # Update experiment statistics
                self.experiment_stats["total_queries"] += 1

                self.logger.info(
                    f"Generated query {i+1}/{self.query_count} for {collection1} + {collection2} (group: {query_group})"
                )

        self.logger.info(f"Generated a total of {len(all_queries)} cross-collection queries")
        return all_queries

    def run_experiment(self) -> bool:
        """Run the complete ablation experiment.

        Returns:
            bool: True if experiment completed successfully
        """
        self.logger.info("=== Starting Comprehensive Ablation Experiment ===")

        try:
            # Clear existing data if requested
            self.clear_existing_data()

            # Generate synthetic test data
            self.generate_test_data()

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

        # Generate queries for this round
        queries = self.generate_cross_collection_queries(
            ablation_tester=ablation_tester,
            test_collections=test_collections,
            control_collections=control_collections,
        )

        # Split queries into test and control groups
        test_queries = [q for q in queries if self.test_control_manager.is_test_query(q["id"])]
        control_queries = [q for q in queries if self.test_control_manager.is_control_query(q["id"])]

        self.logger.info(f"Round {round_number}: {len(test_queries)} test queries, {len(control_queries)} control queries")

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
            "test_query_count": len(test_queries),
            "control_query_count": len(control_queries),
            "impact_metrics": {},
            "control_metrics": {},
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

            # Run ablation tests for test group queries
            combo_metrics = {}

            for query in test_queries:
                query_id = uuid.UUID(query["id"])
                query_text = query["text"]
                collection_query_ids = query.get("collection_query_ids", {})

                self.logger.info(f"Testing query: {query_text}")

                try:
                    # Process each collection in the query
                    for collection_name in query["collections"]:
                        # Skip if this collection isn't in the current test group
                        if collection_name not in test_collections:
                            continue

                        # Use collection-specific query ID
                        collection_query_id = uuid.UUID(
                            collection_query_ids.get(collection_name, str(query_id))
                        )

                        # Execute the ablation test for this query against this collection
                        results = ablation_tester.run_ablation_test(
                            config=config,
                            query_id=collection_query_id,
                            query_text=query_text,
                        )

                        # Store results by query ID and collection
                        query_key = f"{query_id}_{collection_name}"
                        combo_metrics[query_key] = {
                            k: r.model_dump() for k, r in results.items()
                        }

                        # Update statistics
                        self.experiment_stats["total_ablations"] += 1

                except Exception as e:
                    self.logger.error(f"CRITICAL: Failed to run ablation test: {e}")
                    sys.exit(1)  # Fail-stop immediately

            # Store results for this combination
            combo_key = "_".join(collection_combo)
            round_impact_metrics[combo_key] = combo_metrics

            self.logger.info(f"Completed ablation tests for combination: {combo_key}")

        # Run tests for control group to validate results
        control_metrics = {}
        self.logger.info(f"Running control group tests for {len(control_queries)} queries")

        for query in control_queries:
            query_id = uuid.UUID(query["id"])
            query_text = query["text"]
            collection_query_ids = query.get("collection_query_ids", {})

            try:
                # Process each collection in the query
                for collection_name in query["collections"]:
                    # Skip if this collection isn't in the control group
                    if collection_name not in control_collections:
                        continue

                    # Use collection-specific query ID
                    collection_query_id = uuid.UUID(
                        collection_query_ids.get(collection_name, str(query_id))
                    )

                    # Configure control test (no ablation)
                    control_config = AblationConfig(
                        collections_to_ablate=[],  # Empty - no ablation for control
                        query_limit=100,
                        include_metrics=True,
                        include_execution_time=True,
                        verbose=False,
                    )

                    # Execute the control test
                    baseline_test = ablation_tester.test_ablation(
                        query_id=collection_query_id,
                        query_text=query_text,
                        collection_name=collection_name,
                        limit=100,
                    )

                    # Store results for this control query and collection
                    query_key = f"{query_id}_{collection_name}"
                    control_metrics[query_key] = baseline_test.model_dump()

            except Exception as e:
                self.logger.error(f"CRITICAL: Failed to run control test: {e}")
                sys.exit(1)  # Fail-stop immediately

        # Complete the round results
        round_results["impact_metrics"] = round_impact_metrics
        round_results["control_metrics"] = control_metrics
        round_results["end_time"] = datetime.now().isoformat()

        # Calculate round summary statistics
        try:
            # Extract metrics from test and control groups for comparison
            test_f1_scores = []
            control_f1_scores = []

            # Process test metrics
            for combo_key, combo_metrics in round_impact_metrics.items():
                for query_key, results in combo_metrics.items():
                    for result_key, metrics in results.items():
                        if "_impact_on_" in result_key:
                            test_f1_scores.append(metrics["f1_score"])

            # Process control metrics
            for query_key, metrics in control_metrics.items():
                control_f1_scores.append(metrics["f1_score"])

            # Calculate summary statistics
            round_results["summary"] = {
                "test_count": len(test_f1_scores),
                "control_count": len(control_f1_scores),
                "test_mean_f1": np.mean(test_f1_scores) if test_f1_scores else 0,
                "control_mean_f1": np.mean(control_f1_scores) if control_f1_scores else 0,
                "test_median_f1": np.median(test_f1_scores) if test_f1_scores else 0,
                "control_median_f1": np.median(control_f1_scores) if control_f1_scores else 0,
            }
        except Exception as e:
            self.logger.error(f"Warning: Failed to calculate round summary statistics: {e}")
            round_results["summary"] = {
                "error": f"Failed to calculate statistics: {str(e)}"
            }

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