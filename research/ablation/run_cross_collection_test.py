#!/usr/bin/env python3
"""
Run a simple cross-collection ablation test.

This script provides a focused test of the cross-collection functionality
in the ablation testing framework, with minimal setup and data generation.
"""

import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any

# Set up environment
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(os.path.dirname(current_path))
os.environ["INDALEKO_ROOT"] = root_path
sys.path.insert(0, root_path)

# Import required modules
from research.ablation.tests.integration.fixed_relationship_patterns import (
    FixedMusicLocationPattern,
    FixedMusicTaskPattern,
)
from research.ablation.registry.shared_entity_registry import SharedEntityRegistry
from research.ablation.ablation_tester import AblationTester, AblationConfig
from db.db_config import IndalekoDBConfig


def setup_database():
    """Set up the database connection and test collections."""
    logger = logging.getLogger(__name__)
    
    try:
        # Connect to the database
        db_config = IndalekoDBConfig()
        db = db_config.get_arangodb()
        logger.info("Successfully connected to ArangoDB database")
        
        # Create test collections if they don't exist
        collections = [
            "AblationMusicActivity", 
            "AblationLocationActivity", 
            "AblationTaskActivity", 
            "AblationCollaborationActivity"
        ]
        
        for collection_name in collections:
            if not db.has_collection(collection_name):
                db.create_collection(collection_name)
                logger.info(f"Created collection {collection_name}")
        
        return db, db_config
    
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)  # Fail-stop immediately


def generate_test_data(db, entity_registry):
    """Generate minimal test data for cross-collection queries."""
    logger = logging.getLogger(__name__)
    logger.info("Generating test data with cross-collection relationships")
    
    # Create patterns with shared registry
    music_location_pattern = FixedMusicLocationPattern(entity_registry=entity_registry)
    music_task_pattern = FixedMusicTaskPattern(entity_registry=entity_registry)
    
    # Generate music-location relationships
    location, music = music_location_pattern.generate_music_at_location()
    
    # Store documents
    try:
        # Store location
        db.collection("AblationLocationActivity").insert(location)
        logger.info(f"Inserted location: {location['location_name']}")
        
        # Store music
        db.collection("AblationMusicActivity").insert(music)
        logger.info(f"Inserted music: {music['artist']} - {music['track']}")
    except Exception as e:
        logger.error(f"Failed to insert documents: {e}")
        sys.exit(1)  # Fail-stop immediately
    
    # Generate music-task relationship
    task, music2 = music_task_pattern.generate_music_during_task()
    
    # Store documents
    try:
        # Store task
        db.collection("AblationTaskActivity").insert(task)
        logger.info(f"Inserted task: {task['task_name']}")
        
        # Store music
        db.collection("AblationMusicActivity").insert(music2)
        logger.info(f"Inserted music: {music2['artist']} - {music2['track']}")
    except Exception as e:
        logger.error(f"Failed to insert documents: {e}")
        sys.exit(1)  # Fail-stop immediately
    
    logger.info("Test data generation complete")
    
    # Return the entity IDs for testing
    entities = {
        "location": location,
        "music": music,
        "task": task,
        "music2": music2
    }
    
    return entities


def run_cross_collection_ablation_test(entities):
    """Run a cross-collection ablation test."""
    logger = logging.getLogger(__name__)
    logger.info("Running cross-collection ablation test")
    
    # Create ablation tester
    tester = AblationTester()
    
    # Create test query for music + location
    query_id = uuid.uuid4()
    query_text = f"Find music I listened to at {entities['location']['location_name']}"
    
    # Store the truth data
    tester.store_truth_data(
        query_id,
        "AblationMusicActivity",
        [entities["music"]["_key"]]
    )
    
    # Configure the ablation test
    config = AblationConfig(
        collections_to_ablate=[
            "AblationMusicActivity",
            "AblationLocationActivity"
        ],
        query_limit=10,
        include_metrics=True,
        include_execution_time=True,
        verbose=True
    )
    
    # Run the ablation test
    results = tester.run_ablation_test(config, query_id, query_text)
    
    # Print the results
    logger.info("\nAblation Test Results:")
    for key, result in results.items():
        logger.info(f"{key}:")
        logger.info(f"  Found: {len(result.results)}")
        logger.info(f"  Precision: {result.metrics.precision:.2f}")
        logger.info(f"  Recall: {result.metrics.recall:.2f}")
        logger.info(f"  F1: {result.metrics.f1:.2f}")
    
    return results


def main():
    """Run the cross-collection test."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    
    # Set up the database
    db, db_config = setup_database()
    
    # Create shared entity registry
    entity_registry = SharedEntityRegistry()
    
    # Generate test data
    entities = generate_test_data(db, entity_registry)
    
    # Run the ablation test
    results = run_cross_collection_ablation_test(entities)
    
    logger.info("\nCross-collection test completed successfully")


if __name__ == "__main__":
    main()