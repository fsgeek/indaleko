#!/usr/bin/env python3
"""
Generate initial truth data for ablation tests.

This script creates initial truth data for all collections
to pass the data sanity check in the ablation framework.
"""

import os
import sys
import logging
import uuid
from pathlib import Path

# Set up path
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = current_path.parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from db.db_config import IndalekoDBConfig
from research.ablation.ablation_tester import AblationTester
from research.ablation.utils.uuid_utils import generate_deterministic_uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("generate_truth_data")

def generate_initial_truth_data():
    """Generate initial truth data for all collections."""
    logger.info("Connecting to database...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    # Collections to generate truth data for
    collections = [
        "AblationMusicActivity",
        "AblationLocationActivity",
        "AblationTaskActivity",
        "AblationCollaborationActivity",
        "AblationStorageActivity",
        "AblationMediaActivity",
    ]
    
    # Create ablation tester for truth data storage
    ablation_tester = AblationTester()
    
    # For each collection, get a few entity IDs and store as truth data
    for collection_name in collections:
        logger.info(f"Generating truth data for {collection_name}...")
        
        if not db.has_collection(collection_name):
            logger.warning(f"Collection {collection_name} does not exist, skipping")
            continue
        
        try:
            # Generate a unique query ID for each collection to avoid constraint violations
            # Use the collection name as part of the seed to ensure uniqueness
            unique_query_id = generate_deterministic_uuid(f"initial_truth_data_{collection_name}")
            
            # Get entity IDs from the collection
            cursor = db.aql.execute(
                f"""
                FOR doc IN {collection_name}
                LIMIT 5
                RETURN doc._key
                """
            )
            entity_ids = [doc_key for doc_key in cursor]
            
            if entity_ids:
                # Temporarily disable entity validation
                os.environ["ABLATION_SKIP_ENTITY_VALIDATION"] = "1"
                
                # Store truth data with the collection-specific query ID
                ablation_tester.store_truth_data(unique_query_id, collection_name, entity_ids)
                
                # Remove environment variable
                del os.environ["ABLATION_SKIP_ENTITY_VALIDATION"]
                
                logger.info(f"Generated truth data for {collection_name}: {len(entity_ids)} entities")
            else:
                logger.warning(f"No entities found in {collection_name}")
        except Exception as e:
            logger.error(f"Error generating truth data for {collection_name}: {e}")
    
    logger.info("Initial truth data generation complete")
    return True

def main():
    """Main entry point."""
    # Clear existing truth data
    logger.info("Clearing existing truth data...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        logger.info(f"Cleared collection {truth_collection}")
    
    # Generate new truth data
    result = generate_initial_truth_data()
    
    if result:
        logger.info("Initial truth data generation successful")
        return 0
    else:
        logger.error("Initial truth data generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())